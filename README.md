# AI DevOps Orchestrator + RAG Validation Repository

> **Enterprise-Grade AI-Powered Code Review System**

---

## 📦 This Repository Contains TWO Projects

### 🔧 Project 1: [AI DevOps Orchestrator](AI_DevOps_Orchestrator/)

Our **primary enterprise product** — an intelligent, automated PR review system that:
- Integrates natively with GitHub Actions
- Analyzes code diffs using Llama 3.3 70B (via Groq)
- Reviews for Security, Correctness, Performance, and Maintainability
- Posts detailed review comments directly on PRs
- Blocks merges when critical issues are found
- Completes reviews in **40-60 seconds**

### 🧪 Project 2: [RAG PR Validation Project](RAG_PR_Validation_Project/)

A **sample RAG-based chatbot application** used exclusively to validate the AI PR Review Agent. This is NOT the main product — it serves as a test subject with intentional code quality variations.

---

## 📂 Repository Structure

```
├── AI_DevOps_Orchestrator/       ← Core product (AI PR Review Agent)
├── RAG_PR_Validation_Project/    ← Sample app for validation
├── docs/                         ← Complete enterprise documentation
│   ├── architecture/
│   ├── workflows/
│   ├── agents/
│   ├── reports/
│   ├── diagrams/
│   └── archive/
├── demo_assets/                  ← Demo scripts & presentation materials
└── README.md                     ← This file
```

## 📄 Key Documents

| Document | Location |
|----------|----------|
| **Master Demo Guide** | [docs/AI_DEVOPS_ORCHESTRATOR_DEMO_GUIDE.md](docs/AI_DEVOPS_ORCHESTRATOR_DEMO_GUIDE.md) |
| **Architecture** | [docs/architecture/ARCHITECTURE.md](docs/architecture/ARCHITECTURE.md) |
| **Demo Script** | [demo_assets/DEMO_SCRIPT.md](demo_assets/DEMO_SCRIPT.md) |
| **Demo Checklist** | [demo_assets/DEMO_CHECKLIST.md](demo_assets/DEMO_CHECKLIST.md) |
| **Project Structure** | [docs/architecture/PROJECT_STRUCTURE.md](docs/architecture/PROJECT_STRUCTURE.md) |

## 🚀 Quick Start

```bash
# For the AI DevOps Orchestrator (CI/CD integration):
# Set GROQ_API_KEY in GitHub repository secrets
# The workflow triggers automatically on PRs

# For the RAG Validation Project (local development):
cd RAG_PR_Validation_Project
pip install -r requirements.txt
cp .env.example .env  # Fill in GOOGLE_API_KEY and JWT_SECRET
uvicorn app.main:app --reload
```

## 🏗 Technology Stack

| Component | Technology |
|-----------|-----------|
| AI/LLM | Llama 3.3 70B via Groq Cloud |
| CI/CD | GitHub Actions |
| API Client | OpenAI Python SDK (Groq-compatible) |
| Review Engine | Python 3.11 |
| Version Control | Git + GitHub |
 
