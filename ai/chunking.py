"""
Text chunking utilities for document processing.
Splits large documents into manageable chunks for embedding and retrieval.
"""
from typing import List
import logging

logger = logging.getLogger(__name__)


def chunk_text(
    text: str,
    chunk_size: int = 1024,
    chunk_overlap: int = 200,
    separator: str = "\n\n",
) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: The text to chunk
        chunk_size: Maximum tokens per chunk (approximate)
        chunk_overlap: Number of tokens to overlap between chunks
        separator: Primary separator to split on

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    # Split by primary separator first
    splits = text.split(separator)

    # Merge small chunks and split large ones
    good_splits = []
    for split in splits:
        if len(split) < chunk_size:
            good_splits.append(split)
        else:
            # Split long chunks by sentences
            sentences = split.split(". ")
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) < chunk_size:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        good_splits.append(current_chunk.strip())
                    current_chunk = sentence + ". "
            if current_chunk:
                good_splits.append(current_chunk.strip())

    # Create overlapping chunks
    chunks = []
    for i, chunk in enumerate(good_splits):
        if i == 0:
            chunks.append(chunk)
        else:
            # Add overlap with previous chunk
            previous = good_splits[i - 1]
            overlap_text = previous[-chunk_overlap:] if len(previous) > chunk_overlap else previous
            combined = overlap_text + " " + chunk
            chunks.append(combined.strip())

    # Filter out empty chunks
    chunks = [c.strip() for c in chunks if c.strip()]

    logger.info(f"Chunked text into {len(chunks)} chunks (size={chunk_size}, overlap={chunk_overlap})")
    return chunks


def chunk_text_by_tokens(
    text: str,
    chunk_size: int = 1024,
    chunk_overlap: int = 200,
) -> List[str]:
    """
    Simple word-based chunking (approximates token count).
    
    Args:
        text: The text to chunk
        chunk_size: Approximate tokens per chunk (1 token ≈ 4 chars)
        chunk_overlap: Tokens to overlap

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    # Convert token size to approximate character count (1 token ≈ 4 characters)
    char_chunk_size = chunk_size * 4
    char_overlap = chunk_overlap * 4

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + char_chunk_size
        if end < text_len:
            # Try to break at a sentence or word boundary
            last_period = text.rfind(".", start, end)
            last_space = text.rfind(" ", start, end)
            if last_period > start:
                end = last_period + 1
            elif last_space > start:
                end = last_space + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position with overlap
        start = end - char_overlap if end < text_len else text_len

    logger.info(f"Chunked text into {len(chunks)} chunks (token_size={chunk_size})")
    return chunks
