import json
import logging
import os
from pathlib import Path

import PyPDF2
from celery import shared_task
from docx import Document as DocxDocument
from django.conf import settings

from .models import Document

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text extraction functions
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as fh:
            reader = PyPDF2.PdfReader(fh)
            return ''.join(page.extract_text() or '' for page in reader.pages)
    except Exception as e:
        logger.error(f"Error extracting text from PDF {file_path}: {e}")
        raise


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = DocxDocument(file_path)
        return '\n'.join(paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip())
    except Exception as e:
        logger.error(f"Error extracting text from DOCX {file_path}: {e}")
        raise


def extract_text_from_file(file_path: str) -> str:
    """Extract text from file based on extension"""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == '.pdf':
        return extract_text_from_pdf(file_path)
    elif suffix in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

@shared_task(bind=True, max_retries=3)
def process_document(self, document_id):
    """
    Process uploaded document:
    - Extract text from PDF/DOCX files
    - Update document status to PROCESSING
    """
    try:
        # Get document
        document = Document.objects.get(id=document_id)
        logger.info(f"Processing document_id={document_id}, file={document.file.name}")

        # Extract text from file
        text = extract_text_from_file(document.file.path)
        logger.info(f"Extracted {len(text)} characters from document_id={document_id}")

        # Update document status to PROCESSING
        document.status = 'PROCESSING'
        document.save()

        logger.info(f"Document {document_id} processing completed successfully")

        return {
            'document_id': document_id,
            'status': 'PROCESSING',
            'text_length': len(text)
        }

    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        raise

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        # Update document status to FAILED
        try:
            document = Document.objects.get(id=document_id)
            document.status = 'FAILED'
            document.save()
        except:
            pass
        raise
