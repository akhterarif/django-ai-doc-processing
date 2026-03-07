# AI Document Intelligence API

A Django-based backend system for processing uploaded PDF documents asynchronously, extracting text, and generating AI-powered summaries using OpenAI API.

## Features

- Upload PDF documents via REST API
- Asynchronous processing with Celery and Redis
- Text extraction from PDFs
- AI summarization and key point extraction
- Status tracking and result retrieval
- Webhook notifications on processing completion/failure
- Docker containerization with PostgreSQL

## Tech Stack

- Django 6.0
- Django REST Framework
- Celery
- Redis
- PostgreSQL
- OpenAI API
- Docker

## Setup

1. Clone the repository
2. Copy environment variables:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` with your actual values:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `WEBHOOK_URL`: Optional URL to receive POST notifications on processing completion
3. Run with Docker:
   ```bash
   docker-compose up --build
   ```
4. Or run locally:
   - Install dependencies: `pip install -r requirements.txt`
   - Run migrations: `python manage.py migrate`
   - Start Redis server
   - Run server: `python manage.py runserver`
   - Run Celery worker: `celery -A django_ai_doc_processing worker --loglevel=info`

## API Endpoints

- `POST /api/documents/upload/`: Upload a PDF document
- `GET /api/documents/`: List all documents with analysis if completed
- `GET /api/documents/{id}/`: Get document details and analysis
- `GET /api/documents/{id}/status/`: Get processing status

## Webhook Notifications

When document processing completes (success or failure), a POST request is sent to the configured `WEBHOOK_URL` with JSON payload:

```json
{
  "document_id": 1,
  "status": "completed",
  "summary": "...",
  "key_points": [...],
  "topics": [...]
}
```

For failures:

```json
{
  "document_id": 1,
  "status": "failed",
  "error": "Error message"
}
```

## Frontend

A Next.js + Tailwind frontend is included under the `frontend/` directory. It provides:

- **Upload page** (`/upload`) for submitting PDF files
- **Document list** (`/`) showing current documents and statuses
- **Detail view** (`/documents/[id]`) with summary, key points, and topics

To run the frontend locally:

```bash
cd frontend
npm install
npm run dev
```

Requests to `/api/*` are proxied to the Django backend (default `localhost:8000`).

## Usage

1. Start backend (see earlier instructions).
2. Start frontend as above or via Docker (see next section).

### With Docker Compose

Run everything together:

```bash
sudo docker compose up --build
```

This will start:

- Django web server on port `8000`
- Celery worker
- PostgreSQL on `5432`
- Redis on `6379`
- Next.js frontend on `3000`

You can then navigate to `http://localhost:3000` to access the app.

Fetch endpoints manually if needed:

1. Upload a document:
   ```bash
   curl -X POST -F "file=@document.pdf" http://localhost:8000/api/documents/upload/
   ```
2. Check status:
   ```bash
   curl http://localhost:8000/api/documents/1/status/
   ```
3. Get results:
   ```bash
   curl http://localhost:8000/api/documents/1/
   ```
