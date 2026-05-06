#!/usr/bin/env python
"""
Test script for the chat functionality
"""
import os
import sys
import django
import requests

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_ai_doc_processing.settings')
sys.path.insert(0, '/home/arif/projects/django-ai-doc-processing')
django.setup()

from documents.models import Document, ChatConversation
from documents.tasks import process_chat_question
from ai.llm import check_ollama_status
from ai.chroma import query_document_chunks


def test_chat_workflow():
    """Test the complete chat workflow"""
    print("🧪 Testing Chat Functionality")
    print("=" * 50)

    # Check Ollama status
    print("1. Checking Ollama service...")
    if not check_ollama_status():
        print("❌ Ollama service not running - cannot test chat")
        return False
    print("✅ Ollama service is running")

    # Check for completed documents
    print("\n2. Checking for completed documents...")
    completed_docs = Document.objects.filter(status='COMPLETED')
    if not completed_docs.exists():
        print("❌ No completed documents found - upload and process a document first")
        return False

    document = completed_docs.first()
    print(f"✅ Found completed document: {document.file.name} (ID: {document.id})")

    # Test ChromaDB query
    print("\n3. Testing ChromaDB query...")
    try:
        chunks = query_document_chunks(
            document_id=document.id,
            query_text="What is this document about?",
            top_k=3
        )
        if chunks:
            print(f"✅ Found {len(chunks)} relevant chunks in ChromaDB")
        else:
            print("❌ No chunks found in ChromaDB - document may not have been properly processed")
            return False
    except Exception as e:
        print(f"❌ ChromaDB query failed: {e}")
        return False

    # Test chat conversation creation
    print("\n4. Testing chat conversation creation...")
    try:
        conversation = ChatConversation.objects.create(
            document=document,
            user=document.uploaded_by,
            question="What is the main topic of this document?",
            status='PENDING'
        )
        print(f"✅ Created chat conversation (ID: {conversation.id})")
    except Exception as e:
        print(f"❌ Failed to create conversation: {e}")
        return False

    # Test background task processing
    print("\n5. Testing background task processing...")
    try:
        # Process synchronously for testing (normally this would be async)
        from django.test import override_settings
        with override_settings(CELERY_TASK_ALWAYS_EAGER=True):
            result = process_chat_question(conversation.id)
            print("✅ Chat processing task completed")

            # Refresh conversation from database
            conversation.refresh_from_db()
            if conversation.status == 'COMPLETED' and conversation.answer:
                print(f"✅ Answer generated: {conversation.answer[:100]}...")
                print(f"✅ Sources found: {len(conversation.sources)}")
                return True
            else:
                print(f"❌ Processing failed - status: {conversation.status}")
                return False

    except Exception as e:
        print(f"❌ Task processing failed: {e}")
        return False


def test_chat_api_endpoints():
    """Test the chat API endpoints"""
    print("\n🧪 Testing Chat API Endpoints")
    print("=" * 50)

    # This would require a running Django server
    print("Note: API endpoint testing requires a running Django server")
    print("To test manually:")
    print("1. Start the services: docker compose up")
    print("2. Upload a document via API")
    print("3. Wait for processing to complete")
    print("4. POST to /api/documents/{id}/chat/ with a question")
    print("5. Check status at /api/documents/{id}/chat/{conversation_id}/status/")
    print("6. Get results at /api/documents/{id}/chat/{conversation_id}/")


if __name__ == "__main__":
    print("🚀 Chat Functionality Test Suite")
    print("=" * 50)

    success = test_chat_workflow()

    if success:
        print("\n🎉 All chat functionality tests passed!")
        test_chat_api_endpoints()
    else:
        print("\n❌ Some tests failed. Check the output above for details.")
        sys.exit(1)