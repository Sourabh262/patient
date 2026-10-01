# Patient Glucose Monitoring & AI Clinical Reporting System

A production-grade hospital patient glucose monitoring system built with **FastAPI**, **LangGraph**, **React + TypeScript + Vite**, and **SQLite**.

## Architecture Overview

The system strictly enforces controlled, deterministic data access:

```text
                    React Frontend
                         |
                         | REST API
                         v
                     FastAPI
                         |
                         v
                   LangGraph Agent
                         |
                         v
                        LLM
                         |
                 Structured Tool Calling
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
   Patient Tool    Glucose Tool    Report Tool
          |              |              |
          +--------------+--------------+
                         |
                    Service Layer
                         |
                         v
                      Database
                         |
                         v
                   Patient Data

Report -> Email Service -> Patient Email
```

### Key Principles
- **No Direct Database Access for LLM**: The LLM interacts strictly via validated structured tool calling.
- **Deterministic Computations**: All glucose averages and clinical staging are performed using deterministic Python logic, not LLM estimation.
- **Configurable Thresholds**: Staging rules are configured through environment variables.
- **Zero Secrets in Code**: Environment configuration managed through `.env`.
- **Synthetic Data**: 30 synthetic patient profiles with continuous glucose telemetry.

---

## Directory Structure

```text
├── backend/            # FastAPI application, LangGraph agent, services, and models
│   ├── app/
│   │   ├── core/       # Configuration, logging, settings
│   │   └── main.py     # FastAPI application entrypoint
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── frontend/           # React + TypeScript + Vite user interface
│   ├── src/
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
├── data/               # SQLite database and seed datasets
├── tests/              # End-to-end and unit test suites
└── README.md
```

---

## Quick Start

### Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Backend API documentation will be available at: `http://localhost:8000/api/v1/docs`.

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend UI will be accessible at: `http://localhost:5173`.

### Running Tests
```bash
pytest tests/
```
