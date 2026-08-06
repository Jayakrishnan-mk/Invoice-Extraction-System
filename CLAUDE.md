# CLAUDE.md

Guidance for Claude Code (and future contributors) working in this repository.

## Project

AI-powered invoice extraction system for a construction company. Vendors send PDF
invoices; this app extracts structured data from them with Gemini (structured JSON
output), stores it in PostgreSQL, and exposes it via a FastAPI REST API and a React
frontend. Built as a production-style interview assessment — layered architecture,
proper error handling, Docker, migrations, Swagger docs — but deliberately scoped down
in a few places (see "Deliberate simplifications" below) to fit assessment time
constraints without cutting code quality.

Full design rationale lives in the plan this project was built from:
`C:\Users\Admin\.claude\plans\i-need-to-do-zany-thacker.md` (architecture diagram, DB
schema reasoning, API table, AI workflow, dev plan). This file is the quick-reference
for day-to-day work; consult the plan for "why" on anything not covered here.

## Tech stack

- **Backend**: Python, FastAPI, SQLAlchemy, Alembic, Pydantic, Postgres driver `psycopg`.
- **Database**: PostgreSQL (Docker).
- **AI**: Gemini API (`google-genai` SDK), structured output via `response_schema` —
  never free-form prompting + manual JSON parsing.
- **PDF**: `pdfplumber` (primary), `PyMuPDF` (fallback if no text layer). No OCR unless
  a sample invoice turns out to be a scanned image with no text layer at all.
- **Frontend**: React + Vite, TailwindCSS.
- **Infra**: Docker Compose (db + backend + frontend services).

## Folder structure

```
techjays/
├── CLAUDE.md
├── README.md
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── alembic/versions/            # migrations
│   ├── mock_inbox/                  # sample PDFs simulating incoming vendor emails
│   ├── uploads/                     # stored invoice PDFs (gitignored)
│   ├── app/
│   │   ├── main.py                  # FastAPI app factory, CORS, exception handlers
│   │   ├── config.py                # Pydantic Settings (env vars)
│   │   ├── logging_config.py
│   │   ├── database.py              # SQLAlchemy engine/session
│   │   ├── dependencies.py          # FastAPI Depends
│   │   ├── api/v1/                  # controllers (routers): invoices.py, chat.py
│   │   ├── models/                  # SQLAlchemy ORM models
│   │   ├── schemas/                 # Pydantic schemas (request/response + AI response_schema)
│   │   ├── repositories/            # DB access layer
│   │   ├── services/                # business logic: pdf_service, ai_extraction_service, invoice_service, chat_service
│   │   ├── core/                    # exceptions, exception handlers
│   │   └── utils/
│   └── tests/{unit,integration}/
└── frontend/
    └── src/{api,components,pages,types}/
```

## Layering convention — do not skip layers

`Controller (api/v1/*.py) → Service (services/*.py) → Repository (repositories/*.py) → Model (models/*.py)`

- Controllers: request/response handling, validation via Pydantic schemas, call one service method. No business logic, no direct DB or SQLAlchemy session use.
- Services: business logic and orchestration (e.g. `InvoiceService` calls `PDFService` then `AIExtractionService` then `InvoiceRepository`). Services call repositories, never the DB session directly.
- Repositories: all SQLAlchemy queries live here. Nothing above this layer writes raw queries.
- Models: SQLAlchemy ORM classes only, no business logic.
- Schemas: Pydantic models for API I/O and for the Gemini `response_schema` — kept separate from ORM models.

## Deliberate simplifications (read before "improving" these)

These are intentional scope decisions for this assessment, not oversights:

- **Extraction is synchronous and fail-fast** (upload → extract text → Gemini → validate → save). No async job queue, no partial-parsing/fallback chain. If any step fails, nothing is persisted and the API returns an error for that file — a batch upload of N files can partially succeed cleanly (per-file success/failure), but there is no intermediate "needs review" record.
- **No `processing`/`needs_review` DB status.** `invoices.status` only ever holds `completed` today (row only exists once extraction succeeds). The column exists so a future async flow (e.g. Celery/RQ) could add `processing`/`failed` states without a schema change — don't add those states now.
- **Processing metadata is stored for observability**: `llm_model`, `processed_at`, `processing_time_ms` on the `invoices` row.
- **Logging is basic structured logging** (Python `logging`, one formatter) — no metrics/tracing pipeline.
- **Test scope is intentionally narrow**: `test_pdf_service.py`, `test_ai_extraction_service.py` (unit, mocked Gemini client), `test_invoices_upload_api.py` (integration, success + failure case). Don't add broad coverage beyond this unless asked.
- **Frontend is 3 pages only**: Upload, Invoice List (with filters), Invoice Detail. Minimal Tailwind styling, no custom design system.
- **AI Chat is optional and last.** Only build `chat_service` / `/chat/query` / `ChatPage` after the core (upload → extraction → DB → API → frontend) is done and approved. It's a structured-query-assisted LLM layer (NL question → Gemini produces a constrained filter/aggregation spec via `response_schema` → parameterized SQLAlchemy query → NL answer) — not vector RAG, and never "LLM writes raw SQL" (injection risk).

## Environment variables

Defined in `.env` (copy from `.env.example`): `DATABASE_URL`, `GEMINI_API_KEY`,
`GEMINI_MODEL`, `APP_ENV`, `LOG_LEVEL`, `CORS_ORIGINS`, `UPLOAD_DIR`,
`MAX_UPLOAD_SIZE_MB`, `MOCK_INBOX_DIR`, `VITE_API_BASE_URL`. Loaded via Pydantic `Settings` in
`backend/app/config.py` — never read `os.environ` directly elsewhere.

## Commands

```bash
# Start full stack
docker compose up --build

# Run backend migrations
docker compose exec backend alembic upgrade head

# Create a new migration after model changes
docker compose exec backend alembic revision --autogenerate -m "description"

# Run backend tests
docker compose exec backend pytest

# Backend only, without Docker (if Postgres is reachable)
cd backend && uvicorn app.main:app --reload
```

## Development plan / status

Build order (one module per review checkpoint):

1. [x] Root scaffolding (this file, docker-compose, env files)
2. [x] Backend skeleton (FastAPI app, config, logging, DB connection, Alembic init, `/health`)
3. [x] DB layer (models, first migration, repository CRUD)
4. [x] PDF service + unit tests
5. [x] AI extraction service (Gemini) + unit tests
6. [x] Invoice service + upload/ingest endpoints + integration test
7. [x] List/detail/filter/search endpoints
8. [x] Swagger polish
9. [ ] Frontend (Upload / List / Detail pages)
10. [ ] Dockerize frontend, finalize compose
11. [ ] README finalized, all 3 test files passing
12. [ ] Bonus: AI chat — only if time remains after step 11

Update the checkboxes above as steps complete so future sessions know what's done.
