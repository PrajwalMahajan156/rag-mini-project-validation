# CHEAT SHEET — Document-Based Chatbot Generator

## Architecture at a Glance
- **Backend**: FastAPI (Python)
- **Auth**: OAuth2 + JWT + bcrypt hashing
- **DB**: SQLite (3 tables: `users`, `documents`, `chat_messages`)
- **Vector Store**: FAISS (local, per-document)
- **Embeddings**: Google Gemini Embeddings (`models/gemini-embedding-001`)
- **LLM**: Google Gemini (`gemini-1.5-flash` or `gemini-3-flash-preview`)
- **Frontend**: Vanilla HTML/CSS/JS
- **OCR**: Tesseract + Google Gemini (for images)

## File Responsibilities (One-liner)
| File | Role |
|------|------|
| `app/main.py` | FastAPI app, endpoints, router mounting |
| `app/api/auth.py` | Register, login, JWT validation |
| `app/core/config.py` | Config constants, dir creation |
| `app/core/database.py` | SQLAlchemy engine, session factory |
| `app/core/security.py` | Password hash, JWT create/verify |
| `app/models/models.py` | ORM: User, Document, ChatMessage |
| `app/services/document_loader.py` | Load PDF, DOCX, TXT, CSV, XLSX, PPTX, images → text |
| `app/services/rag_service.py` | Split text → embed → FAISS save/load/query |
| `app/services/chat_service.py` | Retrieve context → Stream LLM → Save to DB & logs |

## Key Classes & Methods

### User Registration & Login Flow
```
register(username, password) 
  → hash password (passlib/bcrypt)
  → store in users table
  → return success

login(username, password)
  → lookup user
  → verify password
  → create JWT (secret key, 24h expiry)
  → return {access_token, token_type}

get_current_user(token)
  → decode JWT
  → lookup User by username
  → return User object (for Depends)
```

### Document Upload & RAG Setup
```
POST /upload (with file, JWT)
  1. Save file to uploads/
  2. DocumentLoader.load_document(path)
     → detect extension
     → call _load_pdf/_load_docx/_load_image etc.
     → return text (fallback: "" on error)
  3. RAGService.process_document(text, doc_id)
     → RecursiveCharacterTextSplitter(chunk_size=1000, overlap=100)
     → FAISS.from_texts(chunks, embeddings) [Google Gemini embeddings]
     → save_local(data/vector_store_{id})
  4. Store Document record in DB (id, filename, user_id)
  5. Return {document_id, filename, message}
```

### Chat & Streaming
```
GET /chat (query, document_id, JWT)
  → ChatService.get_response(query, document_id, session_id, user_id, db, model_id)
    1. RAGService.query_document(query, k=4) → retrieve top 4 chunks from FAISS
    2. DB query: get last 5 ChatMessages for this session
    3. Build system_prompt: context + history + instructions
    4. ChatGoogleGenerativeAI(model, streaming=True)
       → stream chunks via generator
       → yield each chunk to StreamingResponse
       → collect full_response string
    5. Save ChatMessage(user, query) and ChatMessage(bot, response) with tokens
    6. Log entry to data/logs/chat_log_YYYYMMDD.jsonl
  → return StreamingResponse(generator)
```

## Database Schema (Quick View)
```
users
  id (PK)
  username (unique)
  hashed_password
  ↓
  documents (one-to-many)
  chat_messages (one-to-many)

documents
  id (UUID string, PK)
  filename
  user_id (FK → users)
  ↓
  chat_messages (one-to-many)

chat_messages
  id (PK)
  session_id (indexed)
  role ('user' | 'bot')
  content (text)
  timestamp (default now)
  user_id (FK)
  document_id (FK)
  input_tokens (nullable)
  output_tokens (nullable)
```

## Configuration & Env
| Var | Source | Used For |
|-----|--------|----------|
| `GOOGLE_API_KEY` | `.env` | Gemini API (embeddings, LLM, OCR) |
| `JWT_SECRET` | `.env` (fallback: dev key) | Sign/verify JWTs |
| `CHUNK_SIZE` | `config.py` | 1000 chars per text chunk |
| `CHUNK_OVERLAP` | `config.py` | 100 char overlap between chunks |
| `EMBEDDING_MODEL` | `config.py` | `models/gemini-embedding-001` |
| `CHAT_MODEL` | `config.py` | `gemini-3-flash-preview` (or override) |
| `UPLOAD_DIR` | `config.py` | `uploads/` |
| `DATA_DIR` | `config.py` | `data/` (logs + vector stores) |

## Supported File Formats
| Ext | Loader | Notes |
|-----|--------|-------|
| `.pdf` | PyPDF2 | Text extraction; scanned PDFs (no text) return "" |
| `.docx` | python-docx | Extract paragraphs |
| `.txt` | built-in | UTF-8 read |
| `.csv` / `.xlsx` | pandas | Convert to string |
| `.pptx` | python-pptx | Extract text from all shapes |
| `.png`, `.jpg`, etc. | Google Gemini | OCR via LLM; fallback "" on error |

## Streaming & Tokens
- **Streaming**: `ChatGoogleGenerativeAI` with `streaming=True` yields content chunks in real-time.
- **Token Counting**:
  - Attempt to read `usage_metadata.prompt_token_count` and `candidates_token_count` from chunk.
  - Fallback: heuristic ~1 token = 4 chars + 0.75 words, or call `llm.get_num_tokens()`.
  - Store in `input_tokens`, `output_tokens` on `ChatMessage`.

## Logging
- **Location**: `data/logs/chat_log_YYYYMMDD.jsonl` (one entry per query)
- **Fields**: timestamp, document_id, session_id, user_id, query, response, latency, model, input_tokens, output_tokens

## Quick Debug Checklist
- ✓ `.env` has `GOOGLE_API_KEY` and `JWT_SECRET`?
- ✓ `uploads/` and `data/` directories writable?
- ✓ FAISS vector stores saved to `data/vector_store_{id}/`?
- ✓ JWT decoding failing? Check `SECRET_KEY` matches in `auth.py` and `security.py`.
- ✓ Gemini API 429 (quota)? Fallback message shown to user.
- ✓ OCR failing? Fallback is empty string; document will have no content.

## Setup & Run
```bash
# Install
pip install -r requirements.txt

# Create .env
echo "GOOGLE_API_KEY=your_key_here" > .env
echo "JWT_SECRET=your_secret_here" >> .env

# Run dev server
uvicorn app.main:app --reload

# Access
# http://localhost:8000
# http://localhost:8000/docs (Swagger)
```

## To Memorize for Viva
1. **RAG pipeline**: Load → Extract text → Split → Embed → FAISS → Query → Retrieve context → LLM answer.
2. **Auth flow**: Register → Hash password → Login → JWT token → Attach to requests → Verify with `get_current_user`.
3. **Streaming**: LLM yields chunks → `ChatService` yields chunks → FastAPI StreamingResponse → client receives in real-time.
4. **Persistence**: Vector stores saved as FAISS files; chat history in SQLite; logs in JSONL.
5. **Error handling**: API errors (429, network) → user-friendly message; OCR fail → "" (empty); DB fail → HTTPException.

