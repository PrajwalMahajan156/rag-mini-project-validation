import os
import faiss
import numpy as np
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import Config

class RAGService:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model=Config.EMBEDDING_MODEL,
            google_api_key=Config.GOOGLE_API_KEY
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=Config.CHUNK_SIZE,
            chunk_overlap=Config.CHUNK_OVERLAP
        )

    def process_document(self, text: str, document_id: str) -> str:
        """
        Processes text, creates embeddings, and saves to FAISS.
        Returns the path to the saved vector store.
        """
        chunks = self.text_splitter.split_text(text)
        
        # Create vector store
        vector_store = FAISS.from_texts(chunks, self.embeddings)
        
        # Save vector store
        save_path = os.path.join(Config.DATA_DIR, f"vector_store_{document_id}")
        vector_store.save_local(save_path)
        
        return save_path

    def query_document(self, query: str, document_id: str, k: int = 4) -> List[str]:
        """
        Queries the vector store for relevant chunks.
        """
        load_path = os.path.join(Config.DATA_DIR, f"vector_store_{document_id}")
        if not os.path.exists(load_path):
            raise FileNotFoundError(f"Vector store for {document_id} not found.")
        
        vector_store = FAISS.load_local(load_path, self.embeddings, allow_dangerous_deserialization=True)
        docs = vector_store.similarity_search(query, k=k)
        
        return [doc.page_content for doc in docs]

    def get_context_text(self, query: str, document_id: str) -> str:
        """
        Retrieves relevant chunks and joins them into a single context string.
        """
        chunks = self.query_document(query, document_id)
        return "\n\n".join(chunks)
