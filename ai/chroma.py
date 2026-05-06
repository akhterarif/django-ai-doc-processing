"""
ChromaDB integration for vector storage and semantic search.
Stores document chunks as embeddings for efficient retrieval.
"""
import logging
import os
from typing import List, Dict, Any
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

# ChromaDB persistent storage directory
CHROMA_DATA_DIR = os.getenv("CHROMA_DATA_DIR", "/tmp/chroma_data")


def get_chroma_client():
    """Get or initialize ChromaDB client."""
    try:
        client = chromadb.PersistentClient(path=CHROMA_DATA_DIR)
        logger.info(f"Connected to ChromaDB at {CHROMA_DATA_DIR}")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB client at {CHROMA_DATA_DIR}: {e}")
        raise


def get_or_create_collection(collection_name: str):
    """
    Get or create a Chroma collection for a document.
    
    Args:
        collection_name: Unique collection name (e.g., "document_1")
    
    Returns:
        Chroma collection object
    """
    try:
        client = get_chroma_client()
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Got/created collection: {collection_name}")
        return collection
    except Exception as e:
        logger.error(f"Error getting/creating collection {collection_name}: {e}")
        raise


def store_document_chunks(
    document_id: int,
    chunks: List[str],
) -> Dict[str, Any]:
    """
    Store document chunks in ChromaDB with embeddings.
    
    Args:
        document_id: Document ID for collection naming
        chunks: List of text chunks to store
    
    Returns:
        Dict with storage stats
    """
    if not chunks:
        logger.warning(f"No chunks to store for document {document_id}")
        return {"stored": 0, "failed": 0}

    collection_name = f"document_{document_id}"
    
    try:
        collection = get_or_create_collection(collection_name)
        
        # Prepare documents with IDs and metadata
        ids = [f"document_{document_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {"document_id": document_id, "chunk_index": i}
            for i in range(len(chunks))
        ]
        
        # ChromaDB automatically generates embeddings using the default model
        collection.add(
            ids=ids,
            documents=chunks,
            metadatas=metadatas,
        )
        stored_count = collection.count()
        logger.info(f"Stored {len(chunks)} chunks for document {document_id}, collection count={stored_count}")
        return {
            "stored": len(chunks),
            "failed": 0,
            "collection": collection_name,
            "collection_count": stored_count,
        }
    
    except Exception as e:
        logger.error(f"Error storing chunks for document {document_id}: {e}")
        return {"stored": 0, "failed": len(chunks), "error": str(e)}


def query_document_chunks(
    document_id: int,
    query_text: str,
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Retrieve relevant chunks for a query using semantic similarity.
    
    Args:
        document_id: Document ID
        query_text: User query
        top_k: Number of top results to return
    
    Returns:
        List of relevant chunks with metadata
    """
    collection_name = f"document_{document_id}"
    
    try:
        collection = get_or_create_collection(collection_name)
        collection_size = collection.count()
        logger.info(f"Querying collection {collection_name}, size={collection_size}")

        if collection_size == 0:
            logger.warning(f"Chroma collection {collection_name} is empty")
            return []
        
        # Query the collection
        results = collection.query(
            query_texts=[query_text],
            n_results=min(top_k, 10),
            include=['documents', 'distances', 'metadatas'],
        )
        
        # Format results
        formatted_results = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                formatted_results.append({
                    "chunk": doc,
                    "distance": results['distances'][0][i] if results['distances'] else None,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                })
        
        logger.info(f"Retrieved {len(formatted_results)} chunks for document {document_id}")
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error querying chunks for document {document_id}: {e}")
        return []


def delete_document_collection(document_id: int) -> bool:
    """
    Delete all chunks for a document (when document is deleted).
    
    Args:
        document_id: Document ID
    
    Returns:
        True if successful
    """
    collection_name = f"document_{document_id}"
    
    try:
        client = get_chroma_client()
        client.delete_collection(name=collection_name)
        logger.info(f"Deleted collection: {collection_name}")
        return True
    except Exception as e:
        logger.error(f"Error deleting collection {collection_name}: {e}")
        return False


def clear_all_collections() -> bool:
    """
    Clear all ChromaDB collections (use with caution).
    
    Returns:
        True if successful
    """
    try:
        client = get_chroma_client()
        collections = client.list_collections()
        for collection in collections:
            client.delete_collection(name=collection.name)
        logger.info("Cleared all ChromaDB collections")
        return True
    except Exception as e:
        logger.error(f"Error clearing collections: {e}")
        return False
