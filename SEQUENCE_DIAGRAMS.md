# SEQUENCE FLOW DIAGRAMS — Upload, Process, Chat

## Diagram 1: User Registration & Login Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ USER REGISTRATION & LOGIN FLOW                                  │
└─────────────────────────────────────────────────────────────────┘

┌──────┐                                              ┌───────────┐
│Client│                                              │ Backend   │
└──┬───┘                                              └─────┬─────┘
   │                                                        │
   │  POST /auth/register                                  │
   │  {username, password}                                 │
   ├────────────────────────────────────────────────────────>
   │                                                        │
   │                               ┌─ Check username exists?
   │                               │
   │                               ├─ Hash password (bcrypt)
   │                               │
   │                               ├─ INSERT User row in DB
   │                               │
   │ {message: "User created"}     │
   │<────────────────────────────────
   │                                    
   │  (Now login)                        
   │  POST /auth/login                   
   │  {username, password}               
   ├─────────────────────────────────────>
   │                                     │
   │                ┌─ Lookup User by username
   │                │
   │                ├─ verify_password(plain, hashed)
   │                │
   │                ├─ create_access_token({"sub": username})
   │                │  → JWT signed with SECRET_KEY, expires 24h
   │                │
   │{access_token,  │
   │ token_type:    │
   │ "bearer"}      │
   │<────────────────
   │
   │ [Store token in client]
   │
   └────────────────────────────────────────────────────────────

Legend:
  → Request/Call
  ← Response
  ├─ Step/Process
```

---

## Diagram 2: Document Upload & RAG Vector Store Creation

```
┌─────────────────────────────────────────────────────────────────┐
│ DOCUMENT UPLOAD & VECTOR STORE SETUP                            │
└─────────────────────────────────────────────────────────────────┘

┌──────┐                          ┌────────┐    ┌──────────────┐
│Client│                          │Backend │    │FileSystem/DB │
└──┬───┘                          └───┬────┘    └────────┬──────┘
   │                                  │                   │
   │ POST /upload                      │                   │
   │ file=<PDF/DOCX/IMG>              │                   │
   │ Authorization: Bearer <JWT>      │                   │
   ├──────────────────────────────────>                   │
   │                                  │                   │
   │            (validate JWT, get current_user)         │
   │                                  │                   │
   │                           ┌─ Generate UUID document_id
   │                           │
   │                           ├─ Save file to uploads/{id}
   │                           ├──────────────────────────>
   │                           │                           │
   │            ┌──────────────────────────────────────────┤
   │            │ DocumentLoader.load_document(path)       │
   │            │                                          │
   │            ├─ Detect extension (.pdf/.docx/.jpg etc) │
   │            │                                          │
   │            ├─ Switch to appropriate loader:          │
   │            │  • PDF → PyPDF2.extract_text()          │
   │            │  • DOCX → docx.Document.paragraphs      │
   │            │  • Image → Gemini LLM (OCR)             │
   │            │  etc.                                    │
   │            │                                          │
   │            └─ Return: full_text (or "" on error)     │
   │                                                       │
   │            ┌──────────────────────────────────────────┤
   │            │ RAGService.process_document(text, id)   │
   │            │                                          │
   │            ├─ RecursiveCharacterTextSplitter         │
   │            │  → Split into chunks (1000 chars,       │
   │            │     100 overlap)                         │
   │            │                                          │
   │            ├─ GoogleGenerativeAIEmbeddings           │
   │            │  → Embed each chunk (vector 768-dim)    │
   │            │                                          │
   │            ├─ FAISS.from_texts(chunks, embeddings)  │
   │            │  → Build vector index                   │
   │            │                                          │
   │            ├─ vector_store.save_local()              │
   │            │  → Save to data/vector_store_{id}       │
   │            ├────────────────────────────────────────>
   │            │                                          │
   │            ├─ INSERT Document row in DB              │
   │            │  (id, filename, user_id)                │
   │            ├──────────────────────────────────────────>
   │            │                                          │
   │ Success:   │                                          │
   │ {          │                                          │
   │  document_ │                                          │
   │  id,       │                                          │
   │  filename, │                                          │
   │  message   │                                          │
   │ }          │<──────────────────────────────────────────
   │<────────────
   │
   └────────────────────────────────────────────────────────

Persistent State After Upload:
  • File:      uploads/{document_id}.{ext}
  • Vector:    data/vector_store_{document_id}/ (FAISS index)
  • DB:        documents table { id, filename, user_id }
```

---

## Diagram 3: Chat Query & Streaming Response

```
┌─────────────────────────────────────────────────────────────────┐
│ CHAT QUERY & STREAMING RESPONSE                                 │
└─────────────────────────────────────────────────────────────────┘

┌──────┐              ┌────────┐         ┌────────────┐   ┌──────┐
│Client│              │Backend │         │Vector Store│   │  LLM │
│      │              │ FastAPI│         │   (FAISS)  │   │Gemini│
└──┬───┘              └───┬────┘         └─────┬──────┘   └──┬───┘
   │                      │                     │             │
   │ GET /chat            │                     │             │
   │ query=...            │                     │             │
   │ document_id=...      │                     │             │
   │ Authorization:...    │                     │             │
   ├─────────────────────>                      │             │
   │                      │                     │             │
   │           (validate JWT, get current_user) │             │
   │                      │                     │             │
   │     ┌────────────────────────────────────────────────────┤
   │     │ ChatService.get_response()                          │
   │     │                                                     │
   │     ├─ (1) RAGService.query_document(query, id, k=4)    │
   │     │                                                     │
   │     ├────────────────────────────────>                  │
   │     │                                 │                 │
   │     │  ┌─ Load FAISS from disk      │                 │
   │     │  │  data/vector_store_{id}/   │                 │
   │     │  │                             │                 │
   │     │  ├─ Embed query using Gemini │                 │
   │     │  │                             │                 │
   │     │  ├─ Similarity search (k=4)   │                 │
   │     │  │                             │                 │
   │     │  └─ Return top 4 chunks       │                 │
   │     │<────────────────────────────────                 │
   │     │                                                   │
   │     ├─ (2) DB query: get last 5 ChatMessages           │
   │     │  (session_id, user_id, document_id)              │
   │     │                                                   │
   │     ├─ (3) Build system_prompt:                        │
   │     │      "You are a helpful assistant..."            │
   │     │      Context: [chunks joined by \\n\\n]          │
   │     │      History: [last 5 turns]                     │
   │     │      Instructions: [answer based on context]     │
   │     │                                                   │
   │     ├─ (4) ChatGoogleGenerativeAI(streaming=True)      │
   │     │                                                   │
   │     ├──────────────────────────────────────────────────>
   │     │                                                   │  Generate content
   │     │                                                   │  with streaming
   │     │ [Streaming loop: yield chunks as they arrive]    │
   │     │                                                   │<─────┐
   │     │<────────────── Chunk 1: "The answer is..." ──────┤      │
   │ [Recv]                                                  │  Stream
   │ [Display]                                               │  chunks
   │     │<────────────── Chunk 2: " based on..." ──────────┤      │
   │ [Recv]                                                  │      │
   │ [Display]                                               │      │
   │     │<────────────── Chunk 3: " the document." ────────┤      │
   │ [Recv]                                                  │      │
   │ [Display]                                               │      │
   │     │                                                   │      │
   │     │ (Full response collected: full_response string)  │      │
   │     │                                                   │      │
   │     ├─ (5) Save to DB:                                 │      │
   │     │      • ChatMessage(role='user', content=query)   │      │
   │     │      • ChatMessage(role='bot',                   │      │
   │     │        content=full_response, tokens=...)        │      │
   │     │                                                   │      │
   │     ├─ (6) Save log entry to:                          │      │
   │     │      data/logs/chat_log_YYYYMMDD.jsonl           │      │
   │     │      {timestamp, document_id, query,             │      │
   │     │       response, latency, tokens, ...}            │      │
   │     │                                                   │      │
   │     └─ (End of generator)                              │      │
   │                                                         │      │
   │ <End of stream>                                         │      │
   │<──────────────────────────────────────────────────────────────┘
   │
   └────────────────────────────────────────────────────────────────

Persistent State After Chat:
  • DB:    chat_messages table { session_id, role, content, 
                                  input_tokens, output_tokens }
  • Logs:  data/logs/chat_log_YYYYMMDD.jsonl
```

---

## Diagram 4: Complete End-to-End Workflow (Summary)

```
┌──────────────────────────────────────────────────────────────────┐
│ FULL WORKFLOW: REGISTER → UPLOAD → CHAT                         │
└──────────────────────────────────────────────────────────────────┘

User Starts
    │
    ├─→ [1] REGISTER
    │       POST /auth/register
    │       └─→ Hash pwd, store in `users` table
    │
    ├─→ [2] LOGIN
    │       POST /auth/login
    │       └─→ Verify pwd, return JWT token
    │
    ├─→ [3] UPLOAD DOCUMENT
    │       POST /upload (with JWT)
    │       └─→ Save file
    │           ├─→ DocumentLoader extracts text
    │           ├─→ RAGService creates embeddings
    │           ├─→ FAISS saves vector store
    │           └─→ DB stores Document record
    │
    ├─→ [4] REPEAT: CHAT with document
    │       GET /chat (with document_id, JWT)
    │       └─→ RAGService loads vectors
    │           ├─→ Retrieve top chunks
    │           ├─→ Load chat history from DB
    │           ├─→ Build prompt with context
    │           ├─→ Stream LLM response
    │           ├─→ Save messages to DB
    │           └─→ Log activity to file
    │
    └─→ [5] END or upload another document & repeat

Key Data Flows:
  Text:        File → DocumentLoader → RAGService → FAISS
  Query:       User input → RAGService.query_document() → Context
  Context:     FAISS chunks + DB history → Prompt → LLM
  Response:    LLM stream → ChatService → DB + Logs + Client
  State:       Users table, Documents table, ChatMessages table

Key Security:
  - JWT validates user identity
  - Document/Message queries filter by user_id
  - Password hashing protects credentials
```

---

## Key Terms Quick Reference

| Term | Meaning |
|------|---------|
| **RAG** | Retrieval-Augmented Generation: retrieve doc chunks + pass to LLM |
| **FAISS** | Local vector similarity search (in-memory or disk) |
| **Embeddings** | Convert text to fixed-size vectors (768 dims for Gemini) |
| **Streaming** | Send response chunks as they arrive (not all-at-once) |
| **JWT** | JSON Web Token: signed, expiring auth token |
| **bcrypt** | Password hashing algorithm (one-way, salted) |
| **Chunk** | Fixed-size segment of document text (overlap for continuity) |
| **Vector Store** | Index of embeddings for similarity search |
| **Session ID** | Groups messages for one conversation thread |
| **Token** | Unit of text used by LLM (1 token ≈ 4 chars) |

