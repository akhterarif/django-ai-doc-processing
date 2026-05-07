"""
AI service module for LLM interactions using Ollama API.
"""
import os
import requests
import json
from typing import Optional
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_GENERATE_ENDPOINT = f"{OLLAMA_BASE_URL}/api/generate"
# Separate connect and read timeouts: (connect_timeout, read_timeout)
# Read timeout can be high since LLM inference takes time
OLLAMA_CONNECT_TIMEOUT = int(os.getenv("OLLAMA_CONNECT_TIMEOUT", "10"))
OLLAMA_READ_TIMEOUT = int(os.getenv("OLLAMA_READ_TIMEOUT", "300"))
OLLAMA_TIMEOUT = (OLLAMA_CONNECT_TIMEOUT, OLLAMA_READ_TIMEOUT)
OLLAMA_RETRY_TOTAL = int(os.getenv("OLLAMA_RETRY_TOTAL", "3"))
OLLAMA_RETRY_BACKOFF = float(os.getenv("OLLAMA_RETRY_BACKOFF", "1"))


def ask_llm(prompt: str, model: str = "gemma2:9b") -> str:
    """
    Generate a response from the LLM using Ollama API.

    Args:
        prompt: The input prompt to send to the LLM
        model: The model to use (default: gemma2:9b)

    Returns:
        The generated response text

    Raises:
        requests.RequestException: If the API request fails
        ValueError: If the response is invalid
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    session = requests.Session()
    retries = Retry(
        total=OLLAMA_RETRY_TOTAL,
        backoff_factor=OLLAMA_RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"],
    )
    session.mount("http://", HTTPAdapter(max_retries=retries))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    try:
        logger.info(f"Checking Ollama API status at {OLLAMA_BASE_URL}")
        if not check_ollama_status():
            raise ConnectionError(f"Ollama API is not accessible at {OLLAMA_BASE_URL}. Please ensure Ollama is running.")

        logger.info(f"Sending prompt to Ollama API with model {model}, timeout=({OLLAMA_CONNECT_TIMEOUT}s connect, {OLLAMA_READ_TIMEOUT}s read)")
        response = session.post(OLLAMA_GENERATE_ENDPOINT, json=payload, timeout=OLLAMA_TIMEOUT)

        response.raise_for_status()  # Raise an exception for bad status codes

        result = response.json()

        if "response" not in result:
            raise ValueError("Invalid response from Ollama API: missing 'response' field")

        generated_text = result["response"]
        logger.info(f"Successfully received response from Ollama API (length: {len(generated_text)})")
        return generated_text

    except requests.Timeout:
        logger.error("Timeout error when calling Ollama API")
        raise requests.RequestException(
            f"Request to Ollama API timed out after {OLLAMA_READ_TIMEOUT}s (read timeout). Check OLLAMA_READ_TIMEOUT env var."
        )
    except requests.ConnectionError:
        logger.error("Connection error when calling Ollama API")
        raise requests.RequestException(
            f"Could not connect to Ollama API. Make sure Ollama is running at {OLLAMA_BASE_URL}"
        )
    except requests.RequestException as e:
        logger.error(f"Request error when calling Ollama API: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON response from Ollama API: {e}")
        raise ValueError("Invalid JSON response from Ollama API")
    except Exception as e:
        logger.error(f"Unexpected error when calling Ollama API: {e}")
        raise


def check_ollama_status() -> bool:
    """
    Check if Ollama service is running and accessible.

    Returns:
        True if Ollama is accessible, False otherwise
    """
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False