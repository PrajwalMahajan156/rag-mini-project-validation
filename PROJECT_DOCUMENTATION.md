# DocBot AI - Project Documentation

## Project Overview
DocBot AI is a professional, high-performance RAG (Retrieval-Augmented Generation) application designed to transform static documents into interactive, context-aware AI chatbots. Built with a focus on speed, accuracy, and premium user experience.

---

## 🚀 Key Features

### 1. Dynamic Bot Creation
- **Instant Deployment**: Simply upload a document to generate a dedicated AI bot.
- **Contextual Intelligence**: Each bot is specifically trained on the content of its respective document.

### 2. Multi-Format Support
- **Documents**: PDF, DOCX, TXT.
- **Data**: CSV, XLSX.
- **Presentations**: PPTX.
- **Images**: Built-in OCR (Optical Character Recognition) for processing text from images.

### 3. Advanced AI Engine
- **LLM**: Powered by Google Gemini Pro.
- **Retrieval**: Leverages high-density Gemini Embeddings with FAISS vector database for sub-second search results.

---

## 🛠 Recent Improvements & Technical Updates

### UI/UX Polish
- **Sidebar Fixed**: Resolved a critical layout issue where the sidebar was non-scrollable. It now features a sleek, custom-styled scrollbar for easy navigation of active bots.
- **Premium Aesthetics**: Implemented a modern "Glassmorphism" theme with deep blue gradients and interactive hover states.

### Intelligent Tracking
- **Token Usage Monitoring**: Implemented real-time tracking of input and output tokens. This helps users understand the cost and efficiency of their AI interactions.
- **Conversational Memory**: Enhanced the chatbot's ability to remember previous exchanges within a session for more natural dialogue.

---

## 📸 visual Evidence

### Main Dashboard
The dashboard provides a central hub for managing knowledge bases and engaging with bots.

![Main Interface](file:///home/prajwal-mahajan/.gemini/antigravity/brain/6a6ff52c-5073-4d15-b566-7f62366cde12/main_chat_interface_1771396805575.png)

### Interactive Chat & Token Tracking
Demonstration of a bot analyzing a PowerPoint presentation, with live token usage statistics displayed.

![Chat and Tokens](file:///home/prajwal-mahajan/.gemini/antigravity/brain/6a6ff52c-5073-4d15-b566-7f62366cde12/bot_response_and_tokens_1771396926146.png)

---

## 📂 Project Directory Structure

Below is the official folder structure of the DocBot AI project:

```text
.streamlit/
└── config.toml

.env/
├── bin/
├── etc/
├── include/
├── lib/
└── share/

backend/
└── main.py

logging/
└── chat_logs.csv

src/
├── chatbot/
│   ├── conversation_chain.py
│   ├── history_manager.py
│   └── memory.py
├── loader/
│   ├── csv_loader.py
│   ├── db_loader.py
│   ├── doc_loader.py
│   ├── docx_loader.py
│   ├── excel_loader.py
│   ├── images_loader.py
│   ├── pdf_loader.py
│   ├── ppt_loader.py
│   ├── pptx_loader.py
│   ├── textfile_loader.py
│   └── web_loader.py
├── logging/
│   └── logger.py
├── processing/
│   ├── embedding.py
│   ├── splitter.py
│   └── vector_store.py
├── rag/
│   ├── gemini_llm.py
│   ├── prompt_template.py
│   ├── qa_chain.py
│   └── retriever.py
├── summarizer/
│   ├── summarizer.py
│   ├── summary_prompt.py
│   └── summary_styles.py
└── ui/
    ├── chat.py
    ├── login.py
    ├── sidebar.py
    └── styles.py

user_data/
└── [User specific data]

vector db/
└── [Vector database files]
```

---

## 🏗 Technology Stack
- **Backend**: FastAPI (Python 3.9+)
- **AI Framework**: LangChain
- **Models**: Google Gemini 1.5 Flash (Generation & Embeddings)
- **Vector Storage**: FAISS (Facebook AI Similarity Search)
- **Frontend**: Vanilla JS, CSS3, HTML5
- **Deployment**: Uvicorn
