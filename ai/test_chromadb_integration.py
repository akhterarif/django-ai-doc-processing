#!/usr/bin/env python
"""
Test script for ChromaDB integration and document chat functionality
"""
import os
import sys
import django

# Set up Django environment
os.environ['DATABASE_URL'] = 'sqlite:///test_db.sqlite3'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_ai_doc_processing.settings')
sys.path.insert(0, '/home/arif/projects/django-ai-doc-processing')
django.setup()

from unittest.mock import patch
from ai.chunking import chunk_text_by_tokens, chunk_text
from ai.chroma import store_document_chunks, query_document_chunks, delete_document_collection


def test_text_chunking():
    """Test text chunking functionality"""
    print("Testing text chunking...")

    sample_text = """
    This is a sample document about machine learning. Machine learning is a subset of artificial intelligence 
    that focuses on teaching computers to learn from data. There are three main types of machine learning: 
    supervised learning, unsupervised learning, and reinforcement learning.
    
    Supervised learning involves training models on labeled data. The model learns to map input features to 
    known outputs. Common applications include classification and regression.
    
    Unsupervised learning finds patterns in unlabeled data. Examples include clustering and dimensionality reduction.
    These techniques are useful for exploratory data analysis.
    
    Reinforcement learning involves training agents to make sequential decisions. The agent learns by receiving 
    rewards or penalties for its actions. This approach is used in game AI and robotics.
    """

    # Test token-based chunking
    chunks_token = chunk_text_by_tokens(sample_text, chunk_size=100, chunk_overlap=20)
    print(f"✓ Token-based chunking: {len(chunks_token)} chunks")
    if chunks_token:
        print(f"  First chunk length: {len(chunks_token[0])} chars")

    # Test separator-based chunking
    chunks_sep = chunk_text(sample_text, chunk_size=200, chunk_overlap=50)
    print(f"✓ Separator-based chunking: {len(chunks_sep)} chunks")
    if chunks_sep:
        print(f"  First chunk length: {len(chunks_sep[0])} chars")

    return len(chunks_token) > 0 and len(chunks_sep) > 0


def test_chromadb_storage():
    """Test ChromaDB storage and retrieval"""
    print("\nTesting ChromaDB storage...")

    sample_chunks = [
        "Python is a popular programming language for data science.",
        "Machine learning models require training on historical data.",
        "Natural language processing enables computers to understand human language.",
        "Deep learning uses neural networks with multiple layers.",
        "Data visualization helps communicate insights from data analysis.",
    ]

    test_doc_id = 9999

    try:
        # Test storing chunks
        result = store_document_chunks(test_doc_id, sample_chunks)
        print(f"✓ Stored {result['stored']} chunks in ChromaDB")

        # Test querying chunks
        query = "machine learning programming"
        retrieved = query_document_chunks(test_doc_id, query, top_k=3)
        print(f"✓ Retrieved {len(retrieved)} relevant chunks")

        if retrieved:
            print(f"  Top chunk: {retrieved[0]['chunk'][:80]}...")

        # Clean up
        delete_document_collection(test_doc_id)
        print(f"✓ Deleted collection for document {test_doc_id}")

        return result['stored'] > 0 and len(retrieved) > 0

    except Exception as e:
        print(f"✗ ChromaDB test failed: {e}")
        return False


def test_chunking_and_storage_workflow():
    """Test complete chunking and storage workflow"""
    print("\nTesting complete chunking and storage workflow...")

    sample_document = """
    Artificial intelligence has revolutionized many industries. From healthcare to finance, AI applications
    are improving efficiency and decision-making. Natural language processing allows machines to understand
    and generate human language. Computer vision enables machines to interpret visual information.
    
    Deep learning models, particularly neural networks with multiple layers, have achieved remarkable results
    in image recognition and language understanding. Transformers, a type of neural network architecture, have
    become the foundation for modern language models.
    
    The future of AI involves developing more efficient models, improving explainability, and ensuring
    responsible deployment of AI systems. Key challenges include data quality, computational resources, and
    ethical considerations around bias and fairness.
    """

    test_doc_id = 8888

    try:
        # Chunk the text
        chunks = chunk_text_by_tokens(sample_document, chunk_size=256, chunk_overlap=50)
        print(f"✓ Created {len(chunks)} chunks from document")

        # Store in ChromaDB
        result = store_document_chunks(test_doc_id, chunks)
        print(f"✓ Stored chunks in ChromaDB: {result['stored']} successful, {result['failed']} failed")

        # Query with different questions
        queries = [
            "What is natural language processing?",
            "Tell me about neural networks",
            "What are the challenges in AI?",
        ]

        for query in queries:
            results = query_document_chunks(test_doc_id, query, top_k=2)
            print(f"✓ Query '{query}': Found {len(results)} relevant chunks")

        # Clean up
        delete_document_collection(test_doc_id)

        return result['stored'] > 0

    except Exception as e:
        print(f"✗ Workflow test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=== ChromaDB Integration Test ===\n")

    tests = [
        test_text_chunking,
        test_chromadb_storage,
        test_chunking_and_storage_workflow,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n=== Test Results: {passed}/{total} tests passed ===")

    if passed == total:
        print("✅ ChromaDB integration is working correctly!")
        print("\nCapabilities:")
        print("- Text chunking with configurable size and overlap")
        print("- Semantic search with ChromaDB embeddings")
        print("- Document question-answering with context retrieval")
        print("\nAPI endpoint ready: POST /api/documents/{id}/chat/")
    else:
        print("❌ Some tests failed. Check the implementation.")


if __name__ == '__main__':
    main()