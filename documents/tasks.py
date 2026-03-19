import json
import logging
import os

import httpx
import PyPDF2
import requests
from celery import shared_task
from django.conf import settings
from pydantic import BaseModel, ValidationError

from .models import Document, DocumentAnalysis

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic model — validates structured JSON returned by the LLM
# ---------------------------------------------------------------------------

class AnalysisResult(BaseModel):
    summary: str
    key_points: list[str]
    topics: list[str]


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3)
def process_document(self, document_id):
    try:
        document = Document.objects.get(id=document_id)
        document.status = 'processing'
        document.save()
        logger.info(f"document_id={document_id} status=processing")

        text = extract_text_from_pdf(document.file.path)
        result = summarize_with_ai(document_id, text)

        DocumentAnalysis.objects.create(
            document=document,
            summary=result.summary,
            key_points=result.key_points,
            topics=result.topics,
        )

        document.status = 'completed'
        document.save()
        logger.info(f"document_id={document_id} status=completed")

        _send_webhook(document_id, 'completed', result=result)

    except Exception as exc:
        logger.error(f"document_id={document_id} error={exc}")
        try:
            document.status = 'failed'
            document.save()
        except Exception:
            pass
        _send_webhook(document_id, 'failed', error=str(exc))
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_path: str) -> str:
    with open(file_path, 'rb') as fh:
        reader = PyPDF2.PdfReader(fh)
        return ''.join(page.extract_text() or '' for page in reader.pages)


# ---------------------------------------------------------------------------
# AI summarization — calls Ollama's OpenAI-compatible endpoint via httpx
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = (
    "You are a document analysis assistant. "
    "You MUST respond with valid JSON and nothing else — no markdown, no explanation. "
    "The JSON object must have exactly three keys: "
    '"summary" (a concise paragraph summarising the document), '
    '"key_points" (an array of up to 5 short strings), '
    '"topics" (an array of up to 5 single-word or short-phrase strings).'
)

# Phi-4 has a 16k token context window. 6 000 chars ≈ 1 500 tokens — well within budget.
_MAX_CHARS = 6_000


def summarize_with_ai(document_id: int, text: str) -> AnalysisResult:
    """
    Send the document text to Ollama's OpenAI-compatible chat endpoint and
    return a validated AnalysisResult. Raises RuntimeError on any failure so
    the Celery task can retry with exponential back-off.
    """
    base_url = settings.LLM_BASE_URL
    model = settings.LLM_MODEL
    timeout = settings.LLM_TIMEOUT_SECONDS

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Analyse the following document and return the JSON object "
                    f"described in your instructions.\n\nDOCUMENT:\n{text[:_MAX_CHARS]}"
                ),
            },
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 512,
        "temperature": 0.2,
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('LLM_API_KEY', 'ollama')}",
        "Content-Type": "application/json",
    }

    logger.info(f"document_id={document_id} llm_request model={model} base_url={base_url}")

    with httpx.Client(timeout=timeout) as client:
        response = client.post(
            f"{base_url}/chat/completions",
            json=payload,
            headers=headers,
        )

    if response.status_code != 200:
        raise RuntimeError(
            f"LLM endpoint returned HTTP {response.status_code}: {response.text[:200]}"
        )

    raw_content = response.json()["choices"][0]["message"]["content"]
    logger.info(f"document_id={document_id} llm_response_received chars={len(raw_content)}")

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"LLM response was not valid JSON: {exc}") from exc

    try:
        return AnalysisResult(**data)
    except ValidationError as exc:
        raise RuntimeError(f"LLM response failed schema validation: {exc}") from exc


# ---------------------------------------------------------------------------
# Webhook helper
# ---------------------------------------------------------------------------

def _send_webhook(document_id: int, status_val: str, result: AnalysisResult = None, error: str = None):
    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        return
    body = {'document_id': document_id, 'status': status_val}
    if result:
        body.update({
            'summary': result.summary,
            'key_points': result.key_points,
            'topics': result.topics,
        })
    if error:
        body['error'] = error
    try:
        requests.post(webhook_url, json=body, timeout=10)
    except Exception as exc:
        logger.error(f"document_id={document_id} webhook_error={exc}")
