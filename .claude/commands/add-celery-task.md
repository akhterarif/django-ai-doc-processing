# Add Celery Task

Add a new background Celery task for async document processing, following all
production patterns required by this project.

## Arguments
$ARGUMENTS — Description of what the task should do

## Steps

1. **Read** `documents/tasks.py` to understand existing patterns.
2. **Read** `documents/models.py` to identify which fields to update.

3. **Implement** the task in `documents/tasks.py` using this template:

   ```python
   @shared_task(bind=True, max_retries=3)
   def your_task_name(self, document_id: int) -> None:
       logger = logging.getLogger(__name__)
       try:
           doc = Document.objects.get(pk=document_id)
           doc.status = 'processing'
           doc.save(update_fields=['status', 'updated_at'])
           logger.info(f"[your_task_name] Starting document_id={document_id}")

           # --- your logic here ---

           doc.status = 'completed'
           doc.save(update_fields=['status', 'updated_at'])
           logger.info(f"[your_task_name] Completed document_id={document_id}")

           # Webhook notification
           _notify_webhook(document_id, 'completed', result_payload)

       except SomeRetryableError as exc:
           logger.warning(f"[your_task_name] Retrying document_id={document_id}: {exc}")
           raise self.retry(exc=exc, countdown=2 ** self.request.retries)

       except Exception as exc:
           logger.error(f"[your_task_name] Failed document_id={document_id}: {exc}")
           Document.objects.filter(pk=document_id).update(status='failed')
           _notify_webhook(document_id, 'failed', {'error': str(exc)})
           raise
   ```

4. **If new model fields are needed** to store the task output:
   - Update `documents/models.py`
   - Remind the user to run `python manage.py makemigrations documents`

5. **Dispatch** the task from the appropriate view:
   ```python
   your_task_name.delay(document.id)
   ```

6. **Write tests** that:
   - Mock all external calls (`unittest.mock.patch`)
   - Use `@override_settings(CELERY_TASK_ALWAYS_EAGER=True)`
   - Test: success path, failure path, retry behavior (mock raising retryable exception)

7. **Output**:
   - Summary of all files changed
   - Example of manually dispatching the task via Django shell
   - Any new environment variables required
