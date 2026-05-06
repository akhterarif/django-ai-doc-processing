"""
AI service module for LLM interactions using Ollama API.
"""
import os
import requests
import json
from typing import Optional
import logging

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_GENERATE_ENDPOINT = f"{OLLAMA_BASE_URL}/api/generate"


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

    try:
        logger.info(f"Sending prompt to Ollama API with model {model}")
        response = requests.post(OLLAMA_GENERATE_ENDPOINT, json=payload, timeout=60)

        response.raise_for_status()  # Raise an exception for bad status codes

        result = response.json()

        if "response" not in result:
            raise ValueError("Invalid response from Ollama API: missing 'response' field")

        generated_text = result["response"]
        logger.info(f"Successfully received response from Ollama API (length: {len(generated_text)})")
        return generated_text

    except requests.Timeout:
        logger.error("Timeout error when calling Ollama API")
        raise requests.RequestException("Request to Ollama API timed out")
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