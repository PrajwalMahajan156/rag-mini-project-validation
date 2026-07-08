# VIVA Guide — Document-Based Chatbot Generator

This guide lists each important file, its responsibilities, key methods, and the overall request/data flow for viva preparation.

**Project Overview**
- Backend: FastAPI (entry: [app/main.py](app/main.py)).
- Core: configuration, DB, security in `app/core`.
- Models: SQLAlchemy models in `app/models/models.py`.
- Services: document processing, vector store (RAG), and chat streaming in `app/services`.
- Frontend: static files in `static/`.
- Data: uploaded files in `uploads/`, FAISS vector stores in `data/`.

**1) Root files**
- `README.md` — Project description, setup, and high-level architecture.
- `requirements.txt` — Python dependencies (FastAPI, LangChain, Gemini, FAISS, OCR libs).

**2) App entry**
- File: [app/main.py](app/main.py)
  - Purpose: FastAPI app setup, router mounting, static files, main endpoints.
  - Key parts:
    - `rag_service = RAGService()` and `chat_service = ChatService()` — initialize services.
    - `Base.metadata.create_all(bind=engine)` — create DB tables.
    - Endpoints:
      - `GET /` -> serves `static/index.html`.
      - `GET /documents` -> returns user's documents (depends on `get_current_user`).
      - `GET /chat/history` -> returns chat history for a document.
      - `DELETE /chat/history` -> clears chat history for a document.
      - `POST /upload` -> saves file, extracts text via `DocumentLoader.load_document()`, calls `RAGService.process_document()`, stores `Document` in DB.
      - `GET /chat` -> streaming chat endpoint that yields chunks from `ChatService.get_response()`.

**3) API: Authentication**
- File: [app/api/auth.py](app/api/auth.py)
  - Purpose: User registration, login and token-based authentication helper.
  - Key functions:
    - `register(form_data, db)` — creates a new user with hashed password.
    - `login(form_data, db)` — verifies credentials and returns JWT bearer token.
    - `get_current_user(token, db)` — decodes JWT, fetches `User` from DB (used with `Depends`).
  - Security integration: uses `app/core/security.py` for hashing and JWT creation.

**4) Core utilities**
- File: [app/core/config.py](app/core/config.py)
  - Purpose: Central configuration values and directory creation.
  - Key attributes: `GOOGLE_API_KEY`, `UPLOAD_DIR`, `DATA_DIR`, `LOG_DIR`, `CHUNK_SIZE`, `EMBEDDING_MODEL`, `CHAT_MODEL`.

- File: [app/core/database.py](app/core/database.py)
  - Purpose: SQLAlchemy engine, `SessionLocal`, `Base`, and `get_db()` dependency generator.

- File: [app/core/security.py](app/core/security.py)
  - Purpose: Password hashing and JWT helpers.
  - Key functions:
    - `verify_password(plain, hashed)`
    - `get_password_hash(password)`
    - `create_access_token(data, expires_delta)` — returns encoded JWT.
  - Notes: `SECRET_KEY` is read from env `JWT_SECRET` (fallback used in dev).

**5) Models**
- File: [app/models/models.py](app/models/models.py)
  - Purpose: SQLAlchemy ORM models and relationships.
  - Classes & main columns:
    - `User`: `id`, `username`, `hashed_password`, relationships `documents`, `chat_messages`.
    - `Document`: `id (UUID string)`, `filename`, `user_id`, relationship to `owner` and `chat_messages`.
    - `ChatMessage`: `id`, `session_id`, `role`, `content`, `timestamp`, `user_id`, `document_id`, `input_tokens`, `output_tokens`.

**6) Services**
- File: [app/services/document_loader.py](app/services/document_loader.py)
  - Purpose: Read uploaded files into plain text for RAG.
  - Main API: `DocumentLoader.load_document(file_path)` — dispatches based on file extension.
  - Supported loaders:
    - `_load_pdf`, `_load_docx`, `_load_txt`, `_load_tabular` (CSV/XLSX), `_load_pptx`, `_load_image`.
  - OCR: `_load_image` uses Google Gemini model (`Config.CHAT_MODEL`) to extract text from images; falls back to empty string on error.

- File: [app/services/rag_service.py](app/services/rag_service.py)
  - Purpose: Create embeddings, split text, and manage FAISS vector stores.
  - Key methods:
    - `__init__()` — configures `GoogleGenerativeAIEmbeddings` and `RecursiveCharacterTextSplitter`.
    - `process_document(text, document_id)` — splits text, embeds chunks, builds FAISS, saves to `data/vector_store_{id}`.
    - `query_document(query, document_id, k=4)` — loads vector store and returns top `k` chunks.
    - `get_context_text(query, document_id)` — joins retrieved chunks into a single context string.
  - Persistence: vectorstores saved under `data/` (see `Config.DATA_DIR`).

- File: [app/services/chat_service.py](app/services/chat_service.py)
  - Purpose: Orchestrate RAG + LLM and stream responses back to client, while logging to DB.
  - Key methods:
    - `get_response(query, document_id, session_id, user_id, db, model_id)` — generator that:
      1. Retrieves context via `RAGService.get_context_text()`.
      2. Loads recent history from `ChatMessage` table.
      3. Builds `system_prompt` with context and instructions.
      4. Uses `ChatGoogleGenerativeAI` with `streaming=True` to stream chunks and `yield` them.
      5. Stores both user and bot messages in DB with `input_tokens`/`output_tokens` if available.
      6. Logs activity to files in `Config.LOG_DIR` via `_save_log()`.
    - `_format_history_from_db(history)` — formats last 5 turns for prompt.

**7) Data & storage**
- `uploads/` — holds original uploaded files (created in `app/main.py` upload handler).
- `data/` — holds persistent vector stores `vector_store_{document_id}` and logs.
- Logs: Chat logs are JSONL files written to `data/logs/chat_log_YYYYMMDD.jsonl`.

**8) End-to-end flow (short)**
1. User registers/logs in via [app/api/auth.py](app/api/auth.py) -> receives JWT.
2. User hits `POST /upload` ([app/main.py](app/main.py)) with file and bearer token.
3. Server saves file to `uploads/` and calls `DocumentLoader.load_document()`.
4. `RAGService.process_document()` splits text, creates embeddings, saves FAISS vector store at `data/vector_store_{id}`.
5. DB `Document` record is created and linked to the user.
6. User queries `GET /chat` with `document_id` and JWT.
7. `ChatService.get_response()`:
   - Loads context from FAISS via `RAGService.query_document()`.
   - Fetches recent history from DB.
   - Streams LLM output (Gemini) back to client.
   - Saves user & bot messages to DB and logs usage.

**9) Where to change key parameters**
- API keys and secrets: `.env` (read via `Config` and `os.getenv`).
- Embedding model: `Config.EMBEDDING_MODEL` in `app/core/config.py`.
- Chat model default: `Config.CHAT_MODEL`.
- FAISS storage location: `Config.DATA_DIR`.
- Chunk size/overlap: `Config.CHUNK_SIZE`, `Config.CHUNK_OVERLAP`.

**10) Likely viva questions & short answers**
- Q: Explain the RAG pipeline in this project.
  - A: Upload -> Text extraction (`DocumentLoader`) -> Split into chunks -> Create embeddings (`RAGService`) -> Store in FAISS -> At query time retrieve top chunks to build context -> LLM answers using retrieved context.

- Q: Why FAISS and not an external vector DB?
  - A: FAISS is local, simple to persist per document, and works offline for smaller workloads; easier to save/load vector stores as files.

- Q: How is user authentication implemented?
  - A: Username/password stored in `users` table. Passwords hashed with `passlib` (`bcrypt`). JWT tokens created with `create_access_token()` and verified in `get_current_user()`.

- Q: How does streaming work?
  - A: `ChatGoogleGenerativeAI` is created with `streaming=True`. `ChatService.get_response()` yields content chunks as they arrive; the FastAPI endpoint returns a `StreamingResponse` built from that generator.

- Q: Where are tokens counted and stored?
  - A: ChatService attempts to read `usage_metadata` from streaming chunks; falls back to heuristics and calls `llm.get_num_tokens()` where available; tokens saved to `ChatMessage` fields `input_tokens` and `output_tokens`.

- Q: How is OCR handled for images / scanned PDFs?
  - A: `DocumentLoader._load_image()` uses Google Gemini to extract text from images. For scanned PDFs, the current PDF loader notes a placeholder; converting PDF pages to images for OCR would be added.

- Q: Where would you add support for a production DB?
  - A: Update `app/core/database.py` `SQLALCHEMY_DATABASE_URL` to a production database URI (Postgres), and adjust engine creation and env secrets.

**11) Quick commands**
- Install deps: `pip install -r requirements.txt`
- Run dev server: `uvicorn app.main:app --reload`
- Create `.env` with `GOOGLE_API_KEY` and optionally `JWT_SECRET`.

**12) Tips for viva**
- Memorize the end-to-end flow and the responsibilities of `DocumentLoader`, `RAGService`, and `ChatService`.
- Know where models, API keys, and directories are configured (`app/core/config.py`).
- Be ready to explain how streaming and token accounting works and where logs are written.

---

If you want, I can:
- Generate a one-page cheat sheet with bullet points for quick memorization.
- Produce 20 probable viva questions with short answers in flashcard format.
- Create simple diagrams (sequence flow) showing upload -> process -> chat steps.

