# AI-Powered Invoice Extraction System

Automates extraction of structured data (vendor, invoice number, line items, totals, GST)
from construction-vendor invoice PDFs using Gemini structured output, and stores it in
PostgreSQL behind a FastAPI REST API with a React frontend.

See [CLAUDE.md](./CLAUDE.md) for architecture, folder structure, and conventions.

## Prerequisites

- Docker + Docker Compose
- A Gemini API key (https://aistudio.google.com/apikey)

## Setup

1. Copy the env template and fill in your Gemini API key:

   ```bash
   cp .env.example .env
   ```

2. Start the stack:

   ```bash
   docker compose up --build
   ```

3. Services:
   - Backend API: http://localhost:8000
   - Swagger docs: http://localhost:8000/docs
   - Frontend: http://localhost:5173
   - Postgres: localhost:5432

4. Apply database migrations (first run, or after model changes):

   ```bash
   docker compose exec backend alembic upgrade head
   ```

## Running tests

```bash
docker compose exec backend pytest
```

## Project status

See the development plan in [CLAUDE.md](./CLAUDE.md#development-plan--status) for what's
implemented vs. pending.
