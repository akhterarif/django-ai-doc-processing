#!/usr/bin/env python
"""
Test script for Document API endpoints
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, '/home/arif/projects/django-ai-doc-processing')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_ai_doc_processing.settings')
django.setup()

from documents.models import Document
from documents.serializers import DocumentSerializer

def test_document_model():
    """Test that the Document model has the correct fields"""
    print("Testing Document model...")

    # Check if model has the required fields
    fields = [f.name for f in Document._meta.fields]
    required_fields = ['id', 'file', 'uploaded_by', 'created_at', 'status', 'doc_type', 'summary', 'key_points']

    for field in required_fields:
        if field in fields:
            print(f"✓ Field '{field}' exists")
        else:
            print(f"✗ Field '{field}' missing")

    # Check status choices
    status_choices = dict(Document.STATUS_CHOICES)
    expected_statuses = ['UPLOADED', 'PROCESSING', 'COMPLETED', 'FAILED']

    for status in expected_statuses:
        if status in status_choices:
            print(f"✓ Status '{status}' exists")
        else:
            print(f"✗ Status '{status}' missing")

    print("Document model test completed.\n")

def test_document_serializer():
    """Test that the Document serializer works"""
    print("Testing Document serializer...")

    # Create a mock document instance
    from django.contrib.auth import get_user_model
    User = get_user_model()

    # Create a test user if it doesn't exist
    user, created = User.objects.get_or_create(
        email='test@example.com',
        defaults={'email': 'test@example.com'}
    )

    # Create a test document
    document = Document.objects.create(
        file='test.pdf',
        uploaded_by=user,
        status='UPLOADED',
        doc_type='pdf',
        summary='Test summary',
        key_points=['point1', 'point2']
    )

    # Test serializer
    serializer = DocumentSerializer(document)
    data = serializer.data

    print(f"Serialized data keys: {list(data.keys())}")

    # Check required fields in serialized data
    required_keys = ['id', 'file', 'uploaded_by', 'uploaded_by_email', 'created_at', 'status', 'doc_type', 'summary', 'key_points']

    for key in required_keys:
        if key in data:
            print(f"✓ Serialized field '{key}' exists")
        else:
            print(f"✗ Serialized field '{key}' missing")

    # Clean up
    document.delete()
    if created:
        user.delete()

    print("Document serializer test completed.\n")

if __name__ == '__main__':
    # Use SQLite for testing
    os.environ['DATABASE_URL'] = 'sqlite:///db.sqlite3'

    test_document_model()
    test_document_serializer()

    print("All tests completed!")