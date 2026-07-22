from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse, Response
import os
import uuid
from app.core.config import Config
from app.services.document_loader import DocumentLoader
from app.services.rag_service import RAGService
from app.services.chat_service import ChatService
from app.core.database import engine, Base, get_db
from app.models import models
from app.api import auth
from sqlalchemy.orm import Session
from app.api.auth import get_current_user

app = FastAPI(title="Document-Based Chatbot Generator")

# Initialize services
rag_service = RAGService()
chat_service = ChatService()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure folders exist
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.DATA_DIR, exist_ok=True)

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth.router)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)


@app.get("/documents")
async def get_documents(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    docs = (
        db.query(models.Document)
        .filter(models.Document.user_id == current_user.id)
        .all()
    )
    return [{"document_id": d.id, "filename": d.filename} for d in docs]


@app.get("/chat/history")
async def get_chat_history(
    document_id: str = Query(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    history = (
        db.query(models.ChatMessage)
        .filter(
            models.ChatMessage.user_id == current_user.id,
            models.ChatMessage.document_id == document_id,
        )
        .order_by(models.ChatMessage.timestamp.asc())
        .all()
    )

    return [
        {
            "role": m.role,
            "content": m.content,
            "timestamp": m.timestamp.isoformat(),
            "input_tokens": m.input_tokens,
            "output_tokens": m.output_tokens,
        }
        for m in history
    ]


@app.delete("/chat/history")
async def delete_chat_history(
    document_id: str = Query(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db.query(models.ChatMessage).filter(
        models.ChatMessage.user_id == current_user.id,
        models.ChatMessage.document_id == document_id,
    ).delete()
    db.commit()
    return {"message": "Chat history cleared"}


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    document_id = str(uuid.uuid4())
    file_ext = os.path.splitext(file.filename)[1]
    file_path = os.path.join(Config.UPLOAD_DIR, f"{document_id}{file_ext}")

    # Save file
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        # Load and process document
        text = DocumentLoader.load_document(file_path)
        if not text.strip():
            raise HTTPException(
                status_code=400, detail="No readable text found in document."
            )

        # Create vector store
        rag_service.process_document(text, document_id)

        # Save document info to database
        db_doc = models.Document(
            id=document_id, filename=file.filename, user_id=current_user.id
        )
        db.add(db_doc)
        db.commit()

        return {
            "document_id": document_id,
            "filename": file.filename,
            "message": "Document processed and chatbot generated successfully.",
        }
    except Exception as e:
        # Cleanup file on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat")
async def chat(
    query: str = Query(...),
    document_id: str = Query(...),
    session_id: str = Query(None),
    model_id: str = Query("gemini-1.5-flash"),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not session_id:
        session_id = str(uuid.uuid4())

    try:

        def stream_generator():
            for chunk in chat_service.get_response(
                query, document_id, session_id, current_user.id, db, model_id
            ):
                yield chunk

        return StreamingResponse(stream_generator(), media_type="text/plain")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
