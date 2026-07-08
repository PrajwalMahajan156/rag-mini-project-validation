import os
from typing import List, Dict, Any
import PyPDF2
import docx
import pandas as pd
from pptx import Presentation
import google.generativeai as genai
from PIL import Image
from app.core.config import Config

class DocumentLoader:
    @staticmethod
    def load_document(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return DocumentLoader._load_pdf(file_path)
        elif ext == ".docx":
            return DocumentLoader._load_docx(file_path)
        elif ext == ".txt":
            return DocumentLoader._load_txt(file_path)
        elif ext in [".csv", ".xlsx", ".xls"]:
            return DocumentLoader._load_tabular(file_path)
        elif ext in [".pptx", ".ppt"]:
            return DocumentLoader._load_pptx(file_path)
        elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]:
            return DocumentLoader._load_image(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _load_pdf(file_path: str) -> str:
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        
        # If no text extracted, try OCR (scanned PDF)
        if not text.strip():
            # This is a simplified OCR for scanned PDFs. 
            # In a real scenario, we'd convert pages to images first.
            # For now, let's assume we need to handle this via image conversion if it's empty.
            pass 
        return text

    @staticmethod
    def _load_docx(file_path: str) -> str:
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    @staticmethod
    def _load_txt(file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _load_tabular(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".csv":
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
        return df.to_string()

    @staticmethod
    def _load_pptx(file_path: str) -> str:
        prs = Presentation(file_path)
        text = ""
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text += shape.text + "\n"
        return text

    @staticmethod
    def _load_image(file_path: str) -> str:
        """
        Extracts text from an image using Google Gemini 1.5 Flash.
        """
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        model = genai.GenerativeModel(Config.CHAT_MODEL)
        
        try:
            with open(file_path, "rb") as f:
                image_data = f.read()
            
            response = model.generate_content([
                "Extract all visible text from this image. Return ONLY the extracted text, nothing else.",
                {"mime_type": "image/png", "data": image_data}
            ])
            
            return response.text
        except Exception as e:
            print(f"Error in Gemini OCR: {e}")
            return ""

    @staticmethod
    def get_document_metadata(file_path: str) -> Dict[str, Any]:
        return {
            "filename": os.path.basename(file_path),
            "size": os.path.getsize(file_path),
            "extension": os.path.splitext(file_path)[1].lower()
        }
