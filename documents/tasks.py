import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path

import PyPDF2
import requests
from celery import shared_task
from docx import Document as DocxDocument
from django.conf import settings

from ai.llm import ask_llm
from ai.chunking import chunk_text_by_tokens
from ai.chroma import store_document_chunks, query_document_chunks
from .models import Document, ChatConversation

logger = logging.getLogger(__name__)

VALID_DOC_TYPES = ['invoice', 'resume', 'legal', 'other']
ANALYSIS_MODEL = 'gemma2:9b'


@dataclass
class AnalysisResult:
    summary: str
    key_points: list
    topics: list = field(default_factory=list)
    doc_type: str = 'other'


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


def build_analysis_prompt(text: str) -> str:
    """Build a prompt that asks the LLM to return structured JSON."""
    return (
        "You are a document analysis assistant. Analyze the following document text and return only valid JSON with the "
        "fields 'summary', 'key_points', and 'doc_type'. 'summary' should be a concise paragraph. "
        "'key_points' should be a list of 3-5 concise bullet points. 'doc_type' must be one of: invoice, resume, legal, other. "
        "If the text is unclear, choose 'other'.\n\n"
        f"Document text:\n{text}"
    )


def parse_json_response(payload: str) -> dict:
    """Parse the raw LLM response and return a JSON object."""
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        start = payload.find('{')
        end = payload.rfind('}')
        if start != -1 and end != -1 and start < end:
            try:
                return json.loads(payload[start:end + 1])
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON payload after cleanup: {e}")
        raise ValueError('LLM returned invalid JSON payload')


def analyze_document_text(text: str, model: str = ANALYSIS_MODEL) -> dict:
    """Generate a structured analysis result from document text."""
    prompt = build_analysis_prompt(text)
    raw_response = ask_llm(prompt, model=model)
    analysis = parse_json_response(raw_response)

    if not isinstance(analysis, dict):
        raise ValueError('LLM response is not a JSON object')

    if 'summary' not in analysis or 'key_points' not in analysis or 'doc_type' not in analysis:
        raise ValueError('LLM response missing required analysis fields')

    if not isinstance(analysis['key_points'], list):
        raise ValueError('LLM response key_points must be a JSON list')

    doc_type = str(analysis['doc_type']).strip().lower()
    if doc_type not in VALID_DOC_TYPES:
        doc_type = 'other'

    return {
        'summary': str(analysis['summary']).strip(),
        'key_points': analysis['key_points'],
        'doc_type': doc_type,
        'topics': analysis.get('topics', []),
    }


def summarize_with_ai(document_id: int, text: str) -> AnalysisResult:
    """Return an AnalysisResult object for the given document text."""
    analysis = analyze_document_text(text)
    return AnalysisResult(
        summary=analysis['summary'],
        key_points=analysis['key_points'],
        topics=analysis.get('topics', []),
        doc_type=analysis['doc_type'],
    )


@shared_task(bind=True, max_retries=3)
def process_document(self, document_id):
    """
    Process uploaded document:
    - Extract text from PDF/DOCX files
    - Generate summary, key points, and document type
    - Chunk text and store embeddings in ChromaDB
    - Save analysis to the document and update status to COMPLETED
    """
    document = None

    try:
        document = Document.objects.get(id=document_id)
        logger.info(f"Processing document_id={document_id}, file={document.file.name}")

        document.status = 'PROCESSING'
        document.save()

        text = extract_text_from_file(document.file.path)
        logger.info(f"Extracted {len(text)} characters from document_id={document_id}")

        # Generate AI analysis
        analysis = analyze_document_text(text)

        # Chunk text and store in ChromaDB
        chunks = chunk_text_by_tokens(text, chunk_size=512, chunk_overlap=100)
        chroma_result = store_document_chunks(document_id, chunks)
        logger.info(f"Stored {chroma_result['stored']} chunks in ChromaDB for document {document_id}")

        if chroma_result['stored'] == 0:
            raise RuntimeError(f"Failed to store embeddings for document {document_id}")

        document.summary = analysis['summary']
        document.key_points = analysis['key_points']
        document.doc_type = analysis['doc_type']
        document.status = 'COMPLETED'
        document.save()

        logger.info(f"Document {document_id} processing completed successfully")

        return {
            'document_id': document_id,
            'status': 'COMPLETED',
            'summary': document.summary,
            'key_points': document.key_points,
            'doc_type': document.doc_type,
            'chunks_stored': chroma_result['stored'],
        }

    except Document.DoesNotExist:
        logger.error(f"Document {document_id} not found")
        raise

    except requests.RequestException as exc:
        logger.error(f"Ollama request failed for document {document_id}: {exc}")
        if document is not None:
            document.status = 'FAILED'
            document.save()
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

    except Exception as e:
        logger.error(f"Error processing document {document_id}: {e}")
        if document is not None:
            document.status = 'FAILED'
            document.save()
        raise


@shared_task(bind=True, max_retries=3)
def process_chat_question(self, conversation_id):
    """
    Process a chat question about a document:
    - Retrieve relevant chunks from ChromaDB
    - Generate answer using LLM with context
    - Save answer and sources to conversation
    """
    conversation = None

    try:
        conversation = ChatConversation.objects.get(id=conversation_id)
        logger.info(f"Processing chat conversation_id={conversation_id}, document_id={conversation.document.id}")

        conversation.status = 'PROCESSING'
        conversation.save()

        # Retrieve relevant chunks from ChromaDB
        chunks = query_document_chunks(
            document_id=conversation.document.id,
            query_text=conversation.question,
            top_k=5
        )

        if not chunks:
            conversation.status = 'FAILED'
            conversation.answer = "No relevant content found for your question in this document."
            conversation.save()
            logger.warning(f"No relevant chunks found for conversation {conversation_id}")
            return {
                'conversation_id': conversation_id,
                'status': 'FAILED',
                'answer': conversation.answer,
            }

        # Build context from retrieved chunks
        context = "\n\n".join([chunk['chunk'] for chunk in chunks])

        # Build prompt with context
        prompt = (
            f"Based on the following document context, answer the user's question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {conversation.question}\n\n"
            f"Answer:"
        )

        # Get answer from LLM
        answer = ask_llm(prompt, model='gemma2:9b')

        # Prepare sources data
        sources = [
            {
                'chunk': chunk['chunk'][:200] + '...' if len(chunk['chunk']) > 200 else chunk['chunk'],
                'distance': chunk['distance'],
            }
            for chunk in chunks
        ]

        # Save results
        conversation.answer = answer
        conversation.sources = sources
        conversation.status = 'COMPLETED'
        conversation.save()

        logger.info(f"Chat conversation {conversation_id} processing completed successfully")

        return {
            'conversation_id': conversation_id,
            'status': 'COMPLETED',
            'answer': answer,
            'sources': sources,
        }

    except ChatConversation.DoesNotExist:
        logger.error(f"Chat conversation {conversation_id} not found")
        raise

    except requests.RequestException as exc:
        logger.error(f"Ollama request failed for conversation {conversation_id}: {exc}")
        if conversation is not None:
            conversation.status = 'FAILED'
            conversation.save()
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

    except Exception as e:
        logger.error(f"Error processing chat conversation {conversation_id}: {e}")
        if conversation is not None:
            conversation.status = 'FAILED'
            conversation.save()
        raise
