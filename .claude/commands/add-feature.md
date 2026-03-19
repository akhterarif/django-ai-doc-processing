# Add Feature

Add a new end-to-end feature to the django-ai-doc-processing project following
all conventions in CLAUDE.md.

## Arguments
$ARGUMENTS — Description of the feature to add

## Steps

1. **Understand the request.** Read CLAUDE.md to confirm conventions. Clarify
   anything ambiguous before writing code.

2. **Read existing code** before adding anything:
   - `documents/models.py` — current schema
   - `documents/migrations/` — latest migration number
   - `documents/views.py` — existing view patterns
   - `documents/tasks.py` — existing task patterns
   - `documents/serializers.py` — existing serializer patterns
   - `documents/urls.py` — existing URL patterns

3. **Determine the change surface** across all layers:
   - New model fields or models → triggers migration
   - New or updated serializer
   - New Celery task (if background work is needed)
   - New view function or ViewSet action
   - New URL pattern

4. **Implement in this order**:
   a. Models (remind user to run `makemigrations documents` afterwards)
   b. Serializers
   c. Tasks — with `@shared_task(bind=True, max_retries=3)`, exponential backoff
      retry, `Document.status` updates at start/end, `logging.info/error` with
      `document_id` context, and webhook notification on completion/failure
   d. Views — function-based `@api_view` for simple endpoints; `ModelViewSet`
      for complex resource logic. Never inline AI/IO — always delegate to tasks.
   e. URL patterns in `documents/urls.py`
   f. Tests in `documents/tests.py` — mock all external calls, use
      `@override_settings(CELERY_TASK_ALWAYS_EAGER=True)`

5. **Output a summary** containing:
   - All files changed and what was changed in each
   - The exact `makemigrations` command if models changed
   - New API endpoint(s) with example `curl` commands
   - Any new environment variables to add to `.env.example`

## Constraints
- All AI/heavy IO must go in Celery tasks, never in views
- Exponential backoff retry on every task calling external APIs
- Mock all external calls in tests — never hit real APIs during tests
- Coverage target ≥ 80% for new code
