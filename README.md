# AI-powered Document-Based Chatbot Generator

A sophisticated system that dynamically creates custom chatbots based on uploaded documents. Built with FastAPI, LangChain, and Google Gemini.

## Features
- **Dynamic Bot Creation**: Automatically generates a chatbot for any uploaded document.
- **Multi-Format Support**: Handles PDF, DOCX, TXT, CSV, XLSX, PPTX, and Images (OCR).
- **Advanced RAG**: Uses Google Gemini Pro for generation and Gemini Embeddings for retrieval.
- **Real-Time Streaming**: Interactive chat experience with streaming responses.
- **Modern UI**: Premium, responsive dashboard for document management and chatting.

## Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd MAIN_PROJECT_FOR_RAG
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Create a `.env` file and add your Google Gemini API Key:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

## Folder Structure
- `app/`: Backend logic (FastAPI, services, core).
- `static/`: Frontend assets (HTML, CSS, JS).
- `uploads/`: Temporary storage for uploaded documents.
- `data/`: Persistent storage for vector indexes and logs.

## Technology Stack
- **Backend**: FastAPI, LangChain, Google Generative AI
- **Vector DB**: FAISS
- **Frontend**: Vanilla HTML/CSS/JS (Premium Aesthetics)
- **OCR**: Tesseract OCR
