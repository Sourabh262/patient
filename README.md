# Patient Glucose Monitoring & AI Clinical Reporting System

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent_Orchestration-blue.svg)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Vite](https://img.shields.io/badge/Vite-5.4+-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![SQLite](https://img.shields.io/badge/Database-SQLite_Async-003B57.svg?logo=sqlite&logoColor=white)](https://www.sqlite.org)
[![Tests](https://img.shields.io/badge/Tests-44_Passing-success.svg)](#running-the-test-suite)

A production-grade hospital patient glucose monitoring and reporting platform built with **FastAPI**, **LangGraph**, **React + TypeScript + Vite**, and **SQLAlchemy Async**.

The system deterministically tracks and groups patient glucose readings across the **latest 4 weeks**, calculates weekly means and clinical glycemic stages, identifies trajectories, synthesizes concise AI clinical summaries, and delivers formal reports directly to the patient's registered email.

---

## 🏛️ Architecture & Strict Isolation Pattern

The LLM **NEVER** interacts directly with the database. Controlled access follows strict unidirectional boundaries:

```text
                         React Frontend
                              |
                              | REST API / JSON
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
         +--------------------+--------------------+
         |                    |                    |
         v                    v                    v
  get_patient()      get_glucose_readings()   generate_report()
  send_email()                                calculate_glucose_report()
         |                    |                    |
         +--------------------+--------------------+
                              |
                        Service Layer
               (Deterministic Calculation Engine)
                              |
                              v
                      Repository Layer
                              |
                              v
                      Database (SQLite)
                              |
                              v
                     Synthetic Cohort (30)

Report -> Email Service -> Patient Email Address
```

### Core Architecture Rules
1. **Zero Database Access for LLM**: The LLM chooses tools exclusively via validated schema-bound tool calling. Tools call backend services, services call repositories, and repositories query the database.
2. **Deterministic Computations**: All 4-week glucose averages, clinical staging, and trend trajectory analyses are calculated using deterministic Python logic—never estimated or calculated by an LLM.
3. **Verified Information Only**: The LLM receives strictly verified calculations and patient data to produce human-readable clinical summaries without hallucination.
4. **Configurable Thresholds**: Glycemic stage cutoffs are configured via environment settings without hardcoded constants in business logic.
5. **Safe Logging & Secrets**: API keys, SMTP credentials, and database URIs reside in `.env`. Logs automatically sanitize patient emails and omit PHI/PII.

---

## 🔬 Clinical Glycemic Classification Engine

Thresholds are configurable in `.env` (defaults conform to standard clinical guidelines):

| Clinical Stage | Threshold Range (mg/dL) | Trend Trajectory Criteria |
| :--- | :--- | :--- |
| **Hypoglycemia** | `< 70.0 mg/dL` | **Improving**: &Delta; &le; -5.0 mg/dL across valid monitoring weeks |
| **Normal** | `70.0 - 99.0 mg/dL` | **Worsening**: &Delta; &ge; +5.0 mg/dL across valid monitoring weeks |
| **Pre-diabetes** | `100.0 - 125.0 mg/dL` | **Stable**: Within &plusmn; 5.0 mg/dL |
| **Diabetes** | `&ge; 126.0 mg/dL` | **Fluctuating**: Reversing trajectories exceeding threshold delta |

---

## 📁 Repository Directory Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── agent/             # LangGraph state graph, nodes, prompts, tools, and mock LLM
│   │   ├── api/               # FastAPI dependency injection, routers, and endpoints
│   │   │   └── v1/endpoints/  # /patients, /reports, /chat
│   │   ├── core/              # Config (pydantic-settings), logging, security middleware
│   │   ├── db/                # SQLAlchemy session, engine, base, and 30-patient seeder
│   │   ├── models/            # Patient, GlucoseReading, Report declarative models
│   │   ├── repositories/      # Patient, Glucose, and Report async data repositories
│   │   ├── schemas/           # Pydantic validation schemas
│   │   └── services/          # PatientService, GlucoseService, ReportService, EmailService, Calculator
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── api/               # Dedicated typed HTTP API client
│   │   ├── components/        # Dashboard, PatientList, PatientProfile, GlucoseChart, ReportCard, AIChat
│   │   ├── types/             # TypeScript interfaces for patients, telemetry, reports
│   │   ├── App.tsx            # Main layout and view router
│   │   └── index.css          # Modern dark-mode glassmorphic design system
│   ├── package.json
│   ├── vite.config.ts
│   └── .env.example
├── data/
│   └── synthetic_patients.json # 30 complete synthetic patient profiles with 4-week telemetry
├── tests/                     # 39 pytest backend tests + 5 frontend Vitest tests
├── Dockerfile.backend
├── Dockerfile.frontend
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Environment Variables

### Backend Configuration (`backend/.env`)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `PROJECT_NAME` | `"Patient Glucose Monitoring & AI Reporting System"` | Display name |
| `ENVIRONMENT` | `"development"` | Environment (`development`, `production`) |
| `DEBUG` | `true` | Debug mode |
| `API_V1_STR` | `"/api/v1"` | API prefix |
| `DATABASE_URL` | `"sqlite+aiosqlite:///./data/patients.db"` | Async SQLite database path |
| `LLM_PROVIDER` | `"mock"` | Provider: `openai`, `google`, or `mock` (offline testing) |
| `OPENAI_API_KEY` | `""` | OpenAI API key (for `gpt-4o-mini`) |
| `GOOGLE_API_KEY` | `""` | Google GenAI API key |
| `SMTP_HOST` | `"smtp.gmail.com"` | SMTP server host |
| `SMTP_PORT` | `587` | SMTP TLS port |
| `SMTP_USER` | `"notifications@hospital-care.org"` | SMTP username |
| `SMTP_PASSWORD` | `""` | SMTP application password |
| `EMAIL_ENABLED` | `false` | `true` to dispatch real emails, `false` for safe simulation |
| `GLUCOSE_HYPO_THRESHOLD` | `70.0` | Hypoglycemia cutoff in mg/dL |
| `GLUCOSE_NORMAL_MAX` | `99.0` | Normal upper limit in mg/dL |
| `GLUCOSE_PREDIABETES_MAX`| `125.0` | Pre-diabetes upper limit in mg/dL |

### Frontend Configuration (`frontend/.env`)

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `"http://localhost:8000/api/v1"` | Target backend REST API endpoint |

---

## 🚀 Quick Start Guide

### Option 1: Docker Compose (Recommended for Production)

```bash
docker compose up --build
```
- Frontend UI: `http://localhost:5173`
- Backend API Docs: `http://localhost:8000/api/v1/docs`
- Health Endpoint: `http://localhost:8000/health`

---

### Option 2: Local Development Setup

#### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt

# Run initial database seeder (seeds 30 synthetic patients)
python -m app.db.seed

# Start FastAPI server
uvicorn app.main:app --reload --port 8000
```
Swagger UI available at: `http://localhost:8000/api/v1/docs`.

#### 2. Frontend Setup
```bash
cd frontend
npm install --legacy-peer-deps
npm run dev
```
Open your browser at: `http://localhost:5173`.

---

## 🧪 Running the Test Suite

### Backend Pytest Suite (39 Comprehensive Tests)
```bash
# Run all backend unit, integration, and agent tests
.\backend\venv\Scripts\pytest tests/
```
Tests cover:
- Database models, CRUD, relationships, cascade deletes, seeder
- Deterministic glucose averages, stages, and 4-week trend trajectories
- LangGraph agent workflow, system prompts, and tool calling
- Controlled tools (`get_patient`, `get_glucose_readings`, `calculate_glucose_report`, `generate_report`, `send_email`)
- Report generation, verified AI summary constraints, and database persistence
- Email service validation, HTML/plain-text templates, and safe simulation
- End-to-end integration flows: `React -> FastAPI -> LangGraph -> Tools -> Services -> Database`

### Frontend Vitest Suite (5 Component Tests)
```bash
cd frontend
npm run test
```

### Frontend Production Build
```bash
cd frontend
npm run build
```

---

## 🔒 Security & Production Hardening
- **Security Headers**: Injected via `SecurityHeadersMiddleware` (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`).
- **Throttling**: In-memory rate limiting protection via `RateLimitMiddleware` (120 req/min per IP).
- **Health Checks**: Live uptime and async database probe at `/health`.
- **Sanitized Logging**: Email masking and exclusion of raw medical telemetry from application log files.
- **Fail-Safe Offline Mode**: Built-in `MockClinicalChatModel` enables offline validation, test execution, and demo functionality without requiring paid third-party API tokens.
