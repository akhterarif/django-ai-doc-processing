# Run Tests

Run the test suite for the django-ai-doc-processing project and report results.

## Arguments
$ARGUMENTS — Optional: specific test module, class, or method (e.g., `documents.tests.DocumentUploadTest`)

## Steps

1. Determine the environment (Docker vs. local):
   - If `docker-compose ps` shows `web` running → use Docker exec
   - Otherwise → run locally

2. **Run tests** (Docker):
   ```bash
   docker-compose exec web python manage.py test documents --verbosity=2
   ```

   **Run tests** (local):
   ```bash
   python manage.py test documents --verbosity=2
   ```

   **Run specific test**:
   ```bash
   python manage.py test $ARGUMENTS --verbosity=2
   ```

3. **Run with coverage** (local):
   ```bash
   coverage run --source='documents' manage.py test documents
   coverage report -m
   ```

4. **Summarize results**:
   - Number of tests: passed / failed / errored
   - Coverage percentage if run with coverage
   - Full traceback for any failures
   - Concrete suggestions to fix each failure

## Notes
- All external AI calls (`openai`, `anthropic`, `requests`) must be mocked —
  never hit real APIs in tests
- Use `@override_settings(CELERY_TASK_ALWAYS_EAGER=True)` to run Celery tasks
  synchronously in tests
- Small PDF fixtures (< 10 KB) for file upload tests should live in
  `documents/fixtures/test.pdf`
- If tests fail due to missing migrations, run
  `python manage.py makemigrations --check` first
