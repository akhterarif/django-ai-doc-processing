#!/usr/bin/env python
"""
Test script for extended Celery document processing with AI analysis
"""
import os
import sys
import tempfile
import django

# Set environment variables BEFORE importing Django
os.environ['DATABASE_URL'] = 'sqlite:///test_db.sqlite3'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_ai_doc_processing.settings')
sys.path.insert(0, '/home/arif/projects/django-ai-doc-processing')

# Set up Django
django.setup()

from unittest.mock import patch
from documents.tasks import analyze_document_text, summarize_with_ai, process_document
from documents.models import Document
from django.contrib.auth import get_user_model


def test_ai_analysis():
    """Test AI analysis functions"""
    print("Testing AI analysis functions...")

    # Test with mocked LLM response
    mock_response = '{"summary": "This is a test document about AI.", "key_points": ["Point 1", "Point 2", "Point 3"], "doc_type": "other"}'

    with patch('documents.tasks.ask_llm', return_value=mock_response):
        try:
            result = analyze_document_text("Test document text")
            print("✓ AI analysis function works")
            print(f"  Summary: {result['summary']}")
            print(f"  Key points: {result['key_points']}")
            print(f"  Doc type: {result['doc_type']}")
            return True
        except Exception as e:
            print(f"✗ AI analysis test failed: {e}")
            return False


def test_summarize_with_ai():
    """Test summarize_with_ai function"""
    print("\nTesting summarize_with_ai function...")

    mock_response = '{"summary": "Test summary", "key_points": ["Key point 1"], "doc_type": "invoice"}'

    with patch('documents.tasks.ask_llm', return_value=mock_response):
        try:
            result = summarize_with_ai(1, "Test text")
            print("✓ summarize_with_ai function works")
            print(f"  Result type: {type(result)}")
            print(f"  Summary: {result.summary}")
            return True
        except Exception as e:
            print(f"✗ summarize_with_ai test failed: {e}")
            return False


def test_document_processing():
    """Test document processing with mocked AI"""
    print("\nTesting document processing...")

    try:
        # Run migrations
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])

        User = get_user_model()
        user, _ = User.objects.get_or_create(email='test@example.com', defaults={'email': 'test@example.com'})

        # Create test document
        document = Document.objects.create(
            file='test.pdf',
            uploaded_by=user,
            status='UPLOADED'
        )

        # Mock response for AI analysis
        mock_response = '{"summary": "Mock AI summary", "key_points": ["Mock point 1", "Mock point 2"], "doc_type": "invoice"}'

        # Mock the file operations and AI response
        with patch('documents.tasks.extract_text_from_file', return_value='Mock extracted text'), \
             patch('documents.tasks.ask_llm', return_value=mock_response):

            # Test the task
            result = process_document(document.id)

            # Refresh document from database
            document.refresh_from_db()

            print("✓ Document processing completed")
            print(f"  Status: {document.status}")
            print(f"  Summary: {document.summary}")
            print(f"  Key points: {document.key_points}")
            print(f"  Doc type: {document.doc_type}")

            # Clean up
            document.delete()
            user.delete()

            return document.status == 'COMPLETED'

    except Exception as e:
        print(f"✗ Document processing test failed: {e}")
        return False
    finally:
        # Clean up test database
        try:
            os.remove('test_db.sqlite3')
        except:
            pass


def main():
    """Run all tests"""
    print("=== Extended Celery Document Processing Test ===\n")

    tests = [
        test_ai_analysis,
        test_summarize_with_ai,
        test_document_processing,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n=== Test Results: {passed}/{total} tests passed ===")

    if passed == total:
        print("✅ All tests passed! Extended document processing is working.")
        print("\nThe Celery task now:")
        print("- Extracts text from documents")
        print("- Generates AI-powered summaries")
        print("- Identifies key points")
        print("- Classifies document types")
        print("- Saves results to the database")
        print("- Updates status to COMPLETED")
    else:
        print("❌ Some tests failed. Check the implementation.")


if __name__ == '__main__':
    main()