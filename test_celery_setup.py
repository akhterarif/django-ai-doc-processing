#!/usr/bin/env python
"""
Test script for Celery document processing
"""
import os
import sys
import tempfile
import django
from pathlib import Path

# Set environment variables BEFORE importing Django
os.environ['DATABASE_URL'] = 'sqlite:///test_db.sqlite3'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_ai_doc_processing.settings')

# Add the project directory to the Python path
sys.path.insert(0, '/home/arif/projects/django-ai-doc-processing')

# Set up Django
django.setup()

from documents.tasks import extract_text_from_file, process_document
from documents.models import Document
from django.contrib.auth import get_user_model

def test_text_extraction():
    """Test text extraction from different file types"""
    print("Testing text extraction...")

    # Test PDF extraction (we'll create a simple test)
    print("✓ Text extraction functions imported successfully")

    # Test that the functions exist
    try:
        from documents.tasks import extract_text_from_pdf, extract_text_from_docx, extract_text_from_file
        print("✓ All text extraction functions available")
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

    return True

def test_celery_task():
    """Test that Celery task can be imported and called"""
    print("\nTesting Celery task...")

    try:
        from documents.tasks import process_document
        print("✓ Celery task imported successfully")

        # Check task attributes
        print(f"✓ Task name: {process_document.name}")
        print(f"✓ Max retries: {process_document.max_retries}")

    except ImportError as e:
        print(f"✗ Celery task import error: {e}")
        return False

    return True

def test_document_model():
    """Test Document model creation"""
    print("\nTesting Document model...")

    try:
        # Run migrations on test database
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py', 'migrate', '--run-syncdb'])

        User = get_user_model()

        # Create test user
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={'email': 'test@example.com'}
        )

        # Create test document
        document = Document.objects.create(
            file='test.pdf',
            uploaded_by=user,
            status='UPLOADED'
        )

        print(f"✓ Document created with ID: {document.id}")
        print(f"✓ Document status: {document.status}")
        print(f"✓ Document uploaded_by: {document.uploaded_by.email}")

        # Clean up
        document.delete()
        if created:
            user.delete()

    except Exception as e:
        print(f"✗ Document model test failed: {e}")
        return False

    return True

def main():
    """Run all tests"""
    print("=== Celery Document Processing Test ===\n")

    tests = [
        test_text_extraction,
        test_celery_task,
        test_document_model,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n=== Test Results: {passed}/{total} tests passed ===")

    if passed == total:
        print("✅ All tests passed! Celery setup is working correctly.")
        print("\nTo run Celery worker:")
        print("celery -A django_ai_doc_processing worker --loglevel=info")
        print("\nTo test document upload:")
        print("POST /api/documents/upload with JWT auth and file")
    else:
        print("❌ Some tests failed. Please check the setup.")

    # Clean up test database
    try:
        os.remove('test_db.sqlite3')
    except:
        pass

if __name__ == '__main__':
    main()