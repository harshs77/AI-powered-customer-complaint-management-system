# AI-powered-customer-complaint-management-system

AI-Powered Customer Complaint Management System is a web-based application designed for managing pharmaceutical customer complaints. It uses React and Redux for the frontend, FastAPI for backend APIs, LangGraph and Groq LLMs for complaint extraction, completeness checking, risk assessment, and summarization, and MySQL for storing complaint records. Users can upload or enter complaint information, receive AI-assisted analysis, review the extracted details and risk assessment, and save the complaint for future tracking.

## Architecture

```mermaid
                      A[React + Redux] -->|HTTP / Axios| B[FastAPI Backend]

    B --> C[LangGraph AI]
    B --> D[(MySQL Database)]

    C --> E[Extract]
    C --> F[Risk Analysis]
    C --> G[Summary]

    E --> H[Groq / Gemma]
    F --> H
    G --> H

    H --> I[Structured AI Result]

    I --> A

    style A fill:#61DAFB,stroke:#333,color:#000
    style B fill:#009688,stroke:#333,color:#fff
    style C fill:#8B5CF6,stroke:#333,color:#fff
    style D fill:#4479A1,stroke:#333,color:#fff
    style H fill:#F97316,stroke:#333,color:#fff
    style I fill:#22C55E,stroke:#333,color:#fff
```

## Main Components

### Frontend
- **React** – complaint form, file upload, AI assistant, and results UI.
- **Redux Toolkit** – manages complaint form state, AI results, loading/error states, and save status.
- **Axios** – communicates with FastAPI.

### Backend
- **FastAPI** – exposes REST APIs for complaint analysis and CRUD operations.
- **LangGraph** – orchestrates the multi-step AI workflow.
- **Groq / Gemma 2 9B** – performs complaint extraction, risk assessment, and summarization.
- **SQLAlchemy** – database ORM.
- **MySQL** – persists complaints and related information.
- **Rule-based fallback** – existing deterministic extraction logic in `complaint.py` is used when needed.

## Workflow

1. User enters complaint text or uploads a PDF/DOCX/TXT/EML file.
2. React sends the input to FastAPI.
3. FastAPI extracts document text when required.
4. LangGraph starts the complaint workflow.
5. The LLM extracts structured complaint fields.
6. The workflow checks complaint completeness.
7. The LLM generates an AI-assisted risk assessment.
8. The workflow generates a concise complaint summary.
9. FastAPI returns the structured result.
10. Redux updates the complaint form and AI Copilot panel.
11. After user review, the complaint is saved to MySQL.
12. Saved complaints can be retrieved through the complaint history APIs.


## Core API Endpoints

``
GET    /health
GET    /api/complaints
GET    /api/complaints/{id}

POST   /api/complaints/analyze-text
POST   /api/complaints/analyze-file
POST   /api/complaints

PUT    /api/complaints/{id}
DELETE /api/complaints/{id}

## AI Workflow

``
Input
  ↓
Complaint Extraction
  ↓
Completeness Check
  ↓
Risk Assessment
  ↓
Summary Generation
  ↓
Structured Response

