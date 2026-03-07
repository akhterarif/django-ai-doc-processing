from celery import shared_task
import PyPDF2
import openai
import os
from .models import Document, DocumentAnalysis
import logging
import requests

logging.basicConfig(level=logging.INFO)

@shared_task
def process_document(document_id):
    try:
        document = Document.objects.get(id=document_id)
        document.status = 'processing'
        document.save()

        # Extract text from PDF
        text = extract_text_from_pdf(document.file.path)

        # Send to OpenAI for summarization
        summary, key_points, topics = summarize_with_ai(text)

        # Save results
        analysis = DocumentAnalysis.objects.create(
            document=document,
            summary=summary,
            key_points=key_points,
            topics=topics
        )

        document.status = 'completed'
        document.save()

        # Send webhook notification
        webhook_url = os.getenv('WEBHOOK_URL')
        if webhook_url:
            try:
                requests.post(webhook_url, json={
                    'document_id': document.id,
                    'status': 'completed',
                    'summary': summary,
                    'key_points': key_points,
                    'topics': topics
                })
            except Exception as e:
                logging.error(f"Failed to send webhook: {e}")

    except Exception as e:
        document.status = 'failed'
        document.save()
        # Send webhook for failure
        webhook_url = os.getenv('WEBHOOK_URL')
        if webhook_url:
            try:
                requests.post(webhook_url, json={
                    'document_id': document.id,
                    'status': 'failed',
                    'error': str(e)
                })
            except Exception as we:
                logging.error(f"Failed to send webhook: {we}")
        raise e

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page in reader.pages:
            text += page.extract_text()
    return text

def summarize_with_ai(text):
    try:
        logging.info("Starting AI summarization")
        openai.api_key = os.getenv('OPENAI_API_KEY')
        prompt = f"Summarize the following document text, extract key points, and identify main topics:\n\n{text[:4000]}"  # Limit text length

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes documents."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )

        summary = response.choices[0].message.content.strip()

        # For simplicity, parse summary into key_points and topics
        # In real implementation, use better parsing
        key_points = summary.split('\n')[:5]  # Assume first 5 lines are key points
        topics = ['Topic1', 'Topic2']  # Placeholder

        return summary, key_points, topics
    except Exception as e:
        logging.error(f"Error in AI summarization: {e}")
        return "Summary not available due to error.", ["Error occurred"], ["Unknown"]