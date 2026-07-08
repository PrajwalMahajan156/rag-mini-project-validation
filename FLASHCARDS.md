# FLASHCARDS — 20 Probable Viva Questions & Answers

## Q1: What is RAG and why is it used in this project?
**A**: RAG (Retrieval-Augmented Generation) combines retrieval and generation. We use it to let the LLM answer questions grounded in a specific document's content—rather than relying on the LLM's general training, we retrieve relevant chunks from the document and pass them as context, ensuring accurate, document-specific answers.

---

## Q2: Explain the document upload flow step-by-step.
**A**: 
1. User uploads file with JWT token → `POST /upload`.
2. Server saves file to `uploads/`.
3. `DocumentLoader.load_document()` extracts text (PDF, DOCX, image, etc.).
4. `RAGService.process_document()` splits text into chunks (1000 chars, 100 overlap).
5. Google Gemini Embeddings converts chunks to vectors.
6. FAISS index created and saved at `data/vector_store_{document_id}`.
7. `Document` record stored in SQLite.
8. Success response returned.

---

## Q3: What does `DocumentLoader.load_document()` do?
**A**: It accepts a file path, detects the extension, and dispatches to the appropriate loader:
- PDF → PyPDF2 (extract pages)
- DOCX → python-docx (extract paragraphs)
- TXT → plain read
- CSV/XLSX → pandas (to_string)
- PPTX → python-pptx (extract text from shapes)
- Images (PNG, JPG) → Google Gemini OCR (extract text via LLM)

---

## Q4: How does FAISS work in this project?
**A**: FAISS is a vector similarity search library. We embed document chunks using Google Gemini Embeddings, store vectors in a FAISS index, and save the index locally. At query time, we load the index, embed the user's query, and perform similarity search to retrieve the top-k (default 4) most relevant chunks.

---

## Q5: Why use Google Gemini Embeddings instead of another embedding model?
**A**: Google Gemini Embeddings is free (with API key), well-optimized, and integrates seamlessly with the LangChain ecosystem. It's also tied to the same API as our LLM, simplifying key management and ensuring consistency.

---

## Q6: How is the context built for the LLM prompt?
**A**: 
1. Retrieve top 4 relevant chunks from FAISS via `RAGService.query_document()`.
2. Join chunks with `\n\n` separator into a single `context_text`.
3. Build `system_prompt` with: context + chat history (last 5 turns) + instructions.
4. Pass prompt to LLM alongside the user query.

---

## Q7: How does streaming work in this project?
**A**: 
1. `ChatGoogleGenerativeAI` is initialized with `streaming=True`.
2. `ChatService.get_response()` is a generator that yields content chunks as they arrive from the LLM.
3. FastAPI wraps the generator in a `StreamingResponse`.
4. Client receives chunks in real-time, building the response incrementally instead of waiting for completion.

---

## Q8: Where are user credentials stored and how are they protected?
**A**: Username and hashed password are stored in the `users` table. Passwords are hashed using `passlib` with `bcrypt` scheme. The `verify_password()` function checks plaintext input against the hashed password. Plaintext passwords are never stored or logged.

---

## Q9: Explain JWT authentication in this project.
**A**: 
1. User logs in with username and password.
2. Server verifies credentials and calls `create_access_token()`.
3. JWT is signed with `SECRET_KEY` and set to expire in 24 hours.
4. Token is returned to client and attached to subsequent requests in the `Authorization: Bearer` header.
5. `get_current_user()` decodes the JWT and verifies the signature; if valid, it returns the `User` object.

---

## Q10: What is the purpose of `session_id` in chat messages?
**A**: `session_id` groups messages for a single conversation thread. It allows users to have multiple chat sessions with the same document. When building the prompt, we fetch only messages from the current `session_id` to maintain conversation context without mixing unrelated chats.

---

## Q11: How are chat messages saved to the database?
**A**: After the LLM responds (streaming complete), `ChatService` creates two `ChatMessage` rows:
1. User message with the query, role='user', no tokens.
2. Bot message with the response, role='bot', with `input_tokens` and `output_tokens` if available.
Both are linked to the same `session_id`, `document_id`, and `user_id` for retrieval later.

---

## Q12: Where and how is activity logged?
**A**: After each chat, `ChatService._save_log()` writes a JSON entry to `data/logs/chat_log_YYYYMMDD.jsonl` (daily file). Each entry contains: timestamp, document_id, session_id, user_id, query, response, latency, model, token counts. This creates an audit trail separate from the database.

---

## Q13: How does token counting work?
**A**: 
1. `ChatService` attempts to read `usage_metadata` from streaming chunks (if API provides it).
2. If unavailable, it calls `llm.get_num_tokens()` to count tokens in the prompt and response.
3. If `get_num_tokens()` returns 0, a fallback heuristic is used: ~1 token per 4 chars + 0.75 words.
4. Counts are stored in `input_tokens` and `output_tokens` fields on `ChatMessage`.

---

## Q14: What are the key configuration parameters and where are they defined?
**A**: 
- `GOOGLE_API_KEY`: Env variable, read in `app/core/config.py` via `os.getenv()`.
- `CHUNK_SIZE` (1000), `CHUNK_OVERLAP` (100): Control text splitting.
- `EMBEDDING_MODEL`, `CHAT_MODEL`: Define which Gemini models to use.
- `UPLOAD_DIR` ("uploads"), `DATA_DIR` ("data"): Storage locations.
- `JWT_SECRET`: Env variable for signing JWTs (fallback: "super-secret-key-for-dev").

---

## Q15: How would you switch from SQLite to PostgreSQL for production?
**A**: 
1. Update `SQLALCHEMY_DATABASE_URL` in `app/core/database.py` to a Postgres connection string (e.g., `postgresql://user:pass@host/dbname`).
2. Install `psycopg2` (Postgres driver).
3. Run migrations or `Base.metadata.create_all()` to set up tables.
4. Store credentials in `.env` and use `os.getenv()`.
5. Optionally add connection pooling with `sqlalchemy.pool.QueuePool`.

---

## Q16: What happens if OCR fails for an image?
**A**: If `DocumentLoader._load_image()` encounters an error (API failure, invalid image), it catches the exception, logs it, and returns an empty string. The document upload succeeds, but the vector store will contain no meaningful content. Queries will retrieve empty or irrelevant chunks.

---

## Q17: What happens if the Gemini API returns a 429 (quota exceeded) error?
**A**: `ChatService.get_response()` catches the error, detects "429" or "quota" in the message, and yields a user-friendly error: *"⚠️ **Gemini API Quota Exceeded.** Please try again in a few moments."* The message is saved to the database as a bot response.

---

## Q18: How does the project enforce user isolation (one user can't see another's documents)?
**A**: 
1. Every `Document` and `ChatMessage` is linked to a `user_id` via foreign key.
2. Endpoints like `GET /documents` and `GET /chat/history` filter by `current_user.id` (obtained via `get_current_user()`).
3. JWT tokens are user-specific; decoding a token extracts the username and looks up the user.
4. No shared resource can be accessed without a valid token for that user.

---

## Q19: Can a user chat with a document uploaded by another user?
**A**: No. When a user queries `GET /chat` with a `document_id`, the backend retrieves the `Document` by ID and implicitly trusts the `document_id` parameter. However, the proper implementation should verify that `current_user.id == document.user_id` before allowing the query. Currently, the code does not enforce this check, which is a potential security issue.

---

## Q20: What improvements would you make to this project for production?
**A**: 
1. **Input validation**: Validate file size, type, and content length limits.
2. **Error handling**: More granular error messages and retry logic.
3. **Security**: Verify user ownership of documents before chat queries; use HTTPS; add rate limiting.
4. **Scalability**: Move vector stores to cloud (S3), use async tasks (Celery), switch to Postgres + connection pooling.
5. **Monitoring**: Add structured logging, metrics (Prometheus), and health checks.
6. **Testing**: Unit tests, integration tests, load tests.
7. **Frontend**: Add loading spinners, error dialogs, document preview before upload.
8. **Caching**: Cache embeddings and FAISS indices in memory for hot documents.

---

