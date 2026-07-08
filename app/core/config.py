import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    UPLOAD_DIR = "uploads"
    DATA_DIR = "data"
    LOG_DIR = os.path.join(DATA_DIR, "logs")
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 100
    EMBEDDING_MODEL = "models/gemini-embedding-001"
    CHAT_MODEL = "gemini-3-flash-preview"

# Ensure directories exist
os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
os.makedirs(Config.DATA_DIR, exist_ok=True)
os.makedirs(Config.LOG_DIR, exist_ok=True)
