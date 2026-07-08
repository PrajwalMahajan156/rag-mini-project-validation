from app.services.document_loader import DocumentLoader
from app.core.config import Config
import os

def test_ocr():
    file_path = "uploads/ocr_test.png"
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
    
    print(f"Testing OCR on: {file_path}")
    try:
        text = DocumentLoader._load_image(file_path)
        print("--- Extracted Text ---")
        print(text)
        print("----------------------")
        if "quick brown fox" in text.lower():
            print("OCR SUCCESS")
        else:
            print("OCR FAILED (text mismatch)")
    except Exception as e:
        print(f"OCR ERROR: {e}")

if __name__ == "__main__":
    test_ocr()
