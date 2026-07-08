import google.generativeai as genai
import json
import os
from typing import List, Dict, Any, Generator
from app.core.config import Config
from app.services.rag_service import RAGService
import time

from langchain_google_genai import ChatGoogleGenerativeAI
from sqlalchemy.orm import Session
from app.models import models
from datetime import datetime

class ChatService:
    def __init__(self):
        self.rag_service = RAGService()

    def get_response(self, query: str, document_id: str, session_id: str, user_id: int, db: Session, model_id: str = None) -> Generator[str, None, None]:
        """
        Generates a streaming response using RAG and dynamic Gemini model.
        """
        if not model_id:
            model_id = Config.CHAT_MODEL
            
        start_time = time.time()
        
        # 1. Retrieve context
        context = self.rag_service.get_context_text(query, document_id)
        
        # 2. Get history from DB
        history = db.query(models.ChatMessage).filter(
            models.ChatMessage.session_id == session_id,
            models.ChatMessage.user_id == user_id,
            models.ChatMessage.document_id == document_id
        ).order_by(models.ChatMessage.timestamp.asc()).all()
        
        # 3. Prompt Engineering
        system_prompt = f"""
You are an intelligent, helpful document-based assistant. Your goal is to answer questions based strictly on the provided context.

Context:
{context}

History:
{self._format_history_from_db(history)}

Instructions:
- Answer only based on the context. If the answer is not in the context, say "I'm sorry, but I couldn't find information about that in the document."
- Be concise but thorough.
- Use a professional and helpful tone.
"""
        
        # 4. Generate Response (Streaming)
        full_response = ""
        input_tokens = 0
        output_tokens = 0
        
        try:
            llm = ChatGoogleGenerativeAI(
                model=model_id,
                google_api_key=Config.GOOGLE_API_KEY,
                streaming=True,
                include_usage_metadata=True
            )
            
            # Pre-calculate input tokens as fallback
            input_tokens = llm.get_num_tokens(f"{system_prompt}\nUser: {query}")
            if input_tokens == 0:
                # Heuristic fallback: 1 token approx 4 chars or 0.75 words
                total_text = f"{system_prompt}\nUser: {query}"
                input_tokens = max(1, len(total_text.split()) + len(total_text) // 10)
            
            for chunk in llm.stream(f"{system_prompt}\nUser: {query}"):
                content = chunk.content
                if isinstance(content, list):
                    content = "".join([part.get("text", "") if isinstance(part, dict) else str(part) for part in content])
                
                full_response += content
                yield content
                
                # Update tokens from metadata if available
                if hasattr(chunk, 'usage_metadata') and chunk.usage_metadata:
                    input_tokens = chunk.usage_metadata.get('prompt_token_count', input_tokens)
                    output_tokens = chunk.usage_metadata.get('candidates_token_count', output_tokens)
            
            # Fallback for output tokens if still 0
            if output_tokens == 0 and full_response:
                output_tokens = llm.get_num_tokens(full_response)
                if output_tokens == 0:
                    output_tokens = max(1, len(full_response.split()) + len(full_response) // 10)

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                friendly_error = "⚠️ **Gemini API Quota Exceeded.** The model is currently unavailable due to high demand. Please try again in a few moments."
                yield friendly_error
                full_response = friendly_error
            else:
                yield f"⚠️ **Connection Error:** {error_msg}"
                full_response = f"Error: {error_msg}"
        
        end_time = time.time()
        
        # 5. Save messages to DB
        user_msg = models.ChatMessage(
            session_id=session_id,
            role="user",
            content=query,
            user_id=user_id,
            document_id=document_id
        )
        bot_msg = models.ChatMessage(
            session_id=session_id,
            role="bot",
            content=full_response,
            user_id=user_id,
            document_id=document_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        db.add(user_msg)
        db.add(bot_msg)
        db.commit()

        # 6. Log activity
        self._save_log({
            "timestamp": time.ctime(start_time),
            "document_id": document_id,
            "session_id": session_id,
            "user_id": user_id,
            "query": query,
            "response": full_response,
            "latency": end_time - start_time,
            "model": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        })

    def _save_log(self, entry: Dict[str, Any]):
        log_file = os.path.join(Config.LOG_DIR, f"chat_log_{time.strftime('%Y%m%d')}.jsonl")
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _format_history_from_db(self, history: List[models.ChatMessage]) -> str:
        formatted = ""
        for msg in history[-5:]: # Keep last 5 turns
            role_label = "User" if msg.role == "user" else "Assistant"
            formatted += f"{role_label}: {msg.content}\n"
        return formatted
