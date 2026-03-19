# Debug Celery

Diagnose and resolve issues with Celery task processing.

## Steps

1. **Check if Celery worker is running**:
   ```bash
   docker-compose ps
   # Look for 'celery' service in 'Up' state
   ```

2. **View recent Celery worker logs**:
   ```bash
   docker-compose logs --tail=100 celery
   ```

3. **Check Redis connectivity** from inside the web container:
   ```bash
   docker-compose exec web python -c "
   import redis
   r = redis.from_url('redis://redis:6379/0')
   print('Redis ping:', r.ping())
   print('Queue length:', r.llen('celery'))
   "
   ```

4. **Inspect active/pending tasks**:
   ```bash
   docker-compose exec web python manage.py shell -c "
   from django_ai_doc_processing.celery import app
   inspect = app.control.inspect()
   print('Active:', inspect.active())
   print('Scheduled:', inspect.scheduled())
   print('Reserved:', inspect.reserved())
   "
   ```

5. **Find documents stuck in 'processing'**:
   ```bash
   docker-compose exec web python manage.py shell -c "
   from documents.models import Document
   from django.utils import timezone
   from datetime import timedelta
   stuck = Document.objects.filter(
       status='processing',
       updated_at__lt=timezone.now() - timedelta(minutes=10)
   )
   print(f'Stuck documents: {stuck.count()}')
   for d in stuck:
       print(f'  id={d.id} updated={d.updated_at}')
   "
   ```

6. **Manually re-trigger processing** for a specific document:
   ```bash
   docker-compose exec web python manage.py shell -c "
   from documents.tasks import process_document
   process_document.delay(<document_id>)
   print('Task dispatched')
   "
   ```

7. **Reset stuck documents** to 'uploaded' so they can be reprocessed:
   ```bash
   docker-compose exec web python manage.py shell -c "
   from documents.models import Document
   from django.utils import timezone
   from datetime import timedelta
   updated = Document.objects.filter(
       status='processing',
       updated_at__lt=timezone.now() - timedelta(minutes=10)
   ).update(status='uploaded')
   print(f'Reset {updated} documents to uploaded')
   "
   ```

## Common Issues & Fixes

| Symptom | Likely Cause | Fix |
|---|---|---|
| `Connection refused redis` | Redis container not running | `docker-compose up redis` |
| `ModuleNotFoundError` | requirements.txt changed after build | `docker-compose down && docker-compose up --build` |
| Task stuck in PENDING forever | Worker not running or broker unreachable | Check `docker-compose ps celery` |
| `kombu.exceptions.EncodeError` | Non-serializable argument passed to task | Only pass primitive types (int, str, dict) to tasks |
| `Task received but worker immediately crashes` | Syntax error in tasks.py | Check `docker-compose logs celery` for traceback |
| `OpenAI AuthenticationError` | Missing or wrong API key | Check `OPENAI_API_KEY` in `.env` |
