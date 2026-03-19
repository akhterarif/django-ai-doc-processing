# Django AI Document Processing — Claude Code Instructions

## Project Overview

Production-style Django REST API for asynchronous AI-powered PDF document processing.
Documents are uploaded via API, queued through Celery/Redis for background processing,
text-extracted with PyPDF2, analysed with OpenAI, and results stored in PostgreSQL.
A Next.js frontend renders results.

**Portfolio target**: Senior/Staff AI Backend Engineering roles. Every new feature
must reflect production-grade patterns — no prototyping shortcuts.

---

## Repository Layout

```
django-ai-doc-processing/
  manage.py
  requirements.txt
  Dockerfile                          # Python 3.12-slim; shared by web + celery
  docker-compose.yml                  # 5 services: db, redis, web, celery, frontend
  django_ai_doc_processing/           # Django project config package
    settings.py                       # All settings; reads from .env via python-dotenv
    celery.py                         # Celery app instance; autodiscovers tasks
    urls.py                           # Root URL conf; mounts /api/documents/
    asgi.py / wsgi.py
  documents/                          # The single Django app
    models.py                         # Document, DocumentAnalysis (+ future models)
    serializers.py                    # DocumentSerializer, DocumentAnalysisSerializer
    views.py                          # Function-based DRF views (upload, list, detail, status)
    tasks.py                          # Celery tasks: process_document, extract_text, summarize
    urls.py                           # /upload, /, /<pk>/, /<pk>/status/
    admin.py                          # Django admin (currently empty — register models here)
    tests.py                          # Tests — must mock all external AI calls
    migrations/                       # Never edit committed migrations
  frontend/                           # Next.js 13 + Tailwind CSS
    pages/
      index.js                        # Document list
      upload.js                       # Upload form
      documents/[id].js               # Document detail
```

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Web framework | Django | 6.0.3 |
| REST API | Django REST Framework | 3.15.2 |
| Async tasks | Celery | 5.4.0 |
| Message broker / result cache | Redis | 7 (Docker) |
| Database | PostgreSQL | 15 (Docker) |
| AI (current) | OpenAI SDK (legacy) | 0.28 |
| PDF parsing | PyPDF2 | 3.0.1 |
| Object storage | boto3 + django-storages | 1.35.0 / 1.14.4 |
| Frontend | Next.js + Tailwind CSS | 13.5.6 / 3 |
| Container | Docker + Docker Compose | — |

---

## Environment Variables

Copy `.env.example` to `.env`. All are loaded in `settings.py` via `python-dotenv`.

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL DSN |
| `CELERY_BROKER_URL` | Yes | Redis broker URL |
| `CELERY_RESULT_BACKEND` | Yes | Redis result backend URL |
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `WEBHOOK_URL` | No | External webhook on task completion |
| `ANTHROPIC_API_KEY` | Roadmap | Claude API key (multi-model feature) |
| `SECRET_KEY` | Yes | Django secret key (move from hardcode to env!) |

---

## Essential Dev Commands

### Local (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Run dev server
python manage.py runserver

# Start Redis (requires local Redis install)
redis-server

# Start Celery worker
celery -A django_ai_doc_processing worker --loglevel=info

# Start Celery beat (periodic tasks)
celery -A django_ai_doc_processing beat --loglevel=info

# Run all tests
python manage.py test documents --verbosity=2

# Run tests with coverage
coverage run --source='documents' manage.py test documents
coverage report -m

# Create migration after model changes
python manage.py makemigrations documents
python manage.py migrate

# Open Django shell
python manage.py shell
```

### Docker (recommended)

```bash
# Build and start all services
docker-compose up --build

# Start in background
docker-compose up -d

# Logs for specific service
docker-compose logs -f celery
docker-compose logs -f web

# Run management commands inside container
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py shell

# Rebuild after requirements.txt change
docker-compose down && docker-compose up --build

# Full reset (destroys DB volume)
docker-compose down -v && docker-compose up --build
```

### Service URLs (Docker)

| Service | URL |
|---|---|
| Django API | http://localhost:8000 |
| Next.js Frontend | http://localhost:3000 |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

---

## Current API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/documents/upload` | Upload PDF (multipart/form-data, field: `file`) |
| `GET` | `/api/documents/` | List all documents with analyses |
| `GET` | `/api/documents/<id>/` | Get document + analysis (if completed) |
| `GET` | `/api/documents/<id>/status/` | Get processing status only |

---

## Code Conventions

### Models (`documents/models.py`)
- Always include `created_at = models.DateTimeField(auto_now_add=True)` and
  `updated_at = models.DateTimeField(auto_now=True)` on every new model.
- Use `JSONField` for structured AI output blobs; use discrete model fields when
  data needs to be filtered or queried.
- For vector fields, use `pgvector` extension via `django-pgvector` (roadmap Feature 3).
- `Document.status` is the canonical state machine: `uploaded → processing → completed | failed`.
  State transitions happen **only inside Celery tasks**, never in views.

### Views (`documents/views.py`)
- Current views are function-based with `@api_view`. New simple endpoints can
  follow this pattern. For complex resource logic, prefer `ModelViewSet`.
- All views must return DRF `Response` objects — never `HttpResponse` directly.
- **Never** perform AI calls, PDF parsing, or heavy I/O inline in views. Always
  dispatch to Celery tasks.

### Tasks (`documents/tasks.py`)
- Decorate with `@shared_task(bind=True, max_retries=3)`.
- On retryable errors (network timeouts, rate limits) use:
  `self.retry(exc=exc, countdown=2 ** self.request.retries)` for exponential backoff.
- Update `Document.status` at task start (`processing`) and end (`completed` / `failed`).
- Log with `logging.info` / `logging.error` including `document_id` in every task.

### Serializers (`documents/serializers.py`)
- Always specify `fields` explicitly — never `fields = '__all__'`.
- Set `read_only_fields` for: `id`, `created_at`, `updated_at`, `status`, and any
  fields populated by AI/Celery tasks.
- Use Pydantic models for internal AI response validation before writing to Django models.

### Settings (`settings.py`)
- No hardcoded secrets. All secrets via `os.getenv()`.
- Group settings by category with header comments (# Celery, # AI, # Storage, etc.).
- New third-party app registrations go at the end of `INSTALLED_APPS`.

### Migrations
- Run `makemigrations documents` after every model change, before committing.
- Never edit migration files already committed to `main`.
- Name migrations descriptively: e.g., `0002_document_add_embedding_field`.

### Tests
- Test file: `documents/tests.py` (split into `tests/` package when > 5 test classes).
- Mock **all** external AI calls with `unittest.mock.patch`.
- Use `@override_settings(CELERY_TASK_ALWAYS_EAGER=True)` to run tasks synchronously.
- Coverage target: ≥ 80% for all new code.

---

## Architecture Notes

- **N+1 query**: `list_documents` currently performs N+1 queries. Fix with
  `Document.objects.select_related('documentanalysis')` when optimizing.
- **OneToOne vs FK**: `DocumentAnalysis` has a OneToOneField. Future multi-analysis
  features (e.g., separate entity extraction, embeddings) should use ForeignKey
  with an `analysis_type` field — not a new OneToOne.
- **Celery worker**: shares the same Docker image as the web service, differentiated
  only by `command` in `docker-compose.yml`.
- **Media files**: stored locally at `/media/`. Production should use S3 via
  `django-storages` (boto3 is already a dependency).

---

## What to Avoid

- **Do NOT** use `openai==0.28` API patterns (`openai.ChatCompletion.create`) on
  new code. The 1.x SDK has a completely different interface. Upgrade together.
- **Do NOT** use `CORS_ALLOW_ALL_ORIGINS = True` in any production config.
- **Do NOT** call AI APIs synchronously in Django views.
- **Do NOT** use `text[:4000]` truncation as a permanent solution for large PDFs.
  Use proper chunking + hierarchical summarization (roadmap Feature 2).
- **Do NOT** store raw API keys in `settings.py` or commit them. The current
  `SECRET_KEY` in `settings.py` is a dev placeholder — replace with env var.
- **Do NOT** skip migrations. Always run `makemigrations` + `migrate` after
  model changes.
- **Do NOT** import Celery tasks at module level in views if it creates circular
  imports — use string task names with `app.send_task()` as a fallback.

---

## Adding a New Feature Checklist

1. Model changes → `python manage.py makemigrations documents` → `migrate`
2. Serializer for new model/fields
3. Celery task if async work is needed (with retries, logging, status updates)
4. View + URL pattern
5. Tests with all external calls mocked
6. Update this `CLAUDE.md` if architecture changes
7. Update `.env.example` if new environment variables are required
