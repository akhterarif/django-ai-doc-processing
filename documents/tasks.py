import json
import logging
import os

import PyPDF2
import requests
import google.generativeai as genai
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
# AI summarization — Google Gemini
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = (
    "You are a document analysis assistant. "
    "You MUST respond with valid JSON and nothing else — no markdown, no code fences, no explanation. "
    "The JSON object must have exactly three keys: "
    '"summary" (a concise paragraph summarising the document), '
    '"key_points" (an array of up to 5 short strings), '
    '"topics" (an array of up to 5 single-word or short-phrase strings). '
    "\n\nAnalyse the following document and return that JSON object."
    "\n\nDOCUMENT:\n{text}"
)

# gemini-2.0-flash has a 1M token context window; 12 000 chars ≈ 3 000 tokens.
_MAX_CHARS = 12_000


def summarize_with_ai(document_id: int, text: str) -> AnalysisResult:
    """
    Send the document text to Google Gemini and return a validated AnalysisResult.
    Raises RuntimeError on any failure so the Celery task can retry with
    exponential back-off.
    """
    api_key = settings.GEMINI_API_KEY
    model_name = settings.GEMINI_MODEL

    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=model_name,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            max_output_tokens=512,
            temperature=0.2,
        ),
    )

    prompt = _PROMPT_TEMPLATE.format(text=text[:_MAX_CHARS])
    logger.info(f"document_id={document_id} gemini_request model={model_name}")

    response = model.generate_content(prompt)
    raw_content = response.text
    logger.info(f"document_id={document_id} gemini_response_received chars={len(raw_content)}")

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Gemini response was not valid JSON: {exc}") from exc

    try:
        return AnalysisResult(**data)
    except ValidationError as exc:
        raise RuntimeError(f"Gemini response failed schema validation: {exc}") from exc


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
