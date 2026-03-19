# Document API

Generate complete, up-to-date API reference documentation for all REST endpoints.

## Steps

1. **Read all sources**:
   - `django_ai_doc_processing/urls.py` — root URL conf
   - `documents/urls.py` — app URL patterns
   - `documents/views.py` — view logic and HTTP methods
   - `documents/serializers.py` — request/response field definitions
   - `documents/models.py` — model fields and choices

2. **For each endpoint**, produce documentation in this exact format:

   ---
   ### `METHOD /path/to/endpoint`
   **Description**: What this endpoint does and when to use it.

   **Request**
   | Field | Location | Type | Required | Description |
   |---|---|---|---|---|
   | `field_name` | body/query/header | string/int/file | yes/no | Description |

   **Success Response (`200`/`201`)**
   ```json
   {
     "field": "example_value"
   }
   ```

   **Error Responses**
   | Status | When | Example |
   |---|---|---|
   | `400` | Validation failure | `{"file": ["No file was submitted."]}` |
   | `404` | Not found | `{"detail": "Not found."}` |

   **Example curl**
   ```bash
   curl -X METHOD http://localhost:8000/path \
     -H "Content-Type: application/json" \
     -d '{"field": "value"}'
   ```
   ---

3. **Add a state machine section**:
   ```
   Document Processing States
   uploaded → processing → completed
                        → failed
   ```
   Explain what triggers each transition.

4. **Add a Webhook Notifications section** with example payloads for both
   `completed` and `failed` events.

5. Output the full documentation in Markdown, ready to paste into `README.md`
   or a dedicated `docs/API.md` file.
