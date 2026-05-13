#!/usr/bin/env python
"""
Test script for the LLM service module
"""
import os
import sys
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_ai_doc_processing.settings')
sys.path.insert(0, '/home/arif/projects/django-ai-doc-processing')
django.setup()

from ai.llm import ask_llm, check_ollama_status


def test_ollama_status():
    """Test if Ollama service is running"""
    print("Testing Ollama service status...")
    if check_ollama_status():
        print("✅ Ollama service is running")
        return True
    else:
        print("❌ Ollama service is not running")
        print("   Make sure Ollama is installed and running:")
        print("   1. Install Ollama: https://ollama.ai/download")
        print("   2. Pull llama3 model: ollama pull llama3")
        print("   3. Start Ollama service")
        return False


def test_llm_function():
    """Test the ask_llm function"""
    print("\nTesting ask_llm function...")

    if not check_ollama_status():
        print("❌ Skipping LLM test - Ollama not running")
        return False

    try:
        prompt = "Hello! Please respond with just 'Hello from Gemma!'"
        print(f"Sending prompt: {prompt}")

        response = ask_llm(prompt, model="gemma2:9b")
        print(f"Response: {response[:100]}...")  # Show first 100 chars

        if response and len(response.strip()) > 0:
            print("✅ LLM function working correctly")
            return True
        else:
            print("❌ LLM returned empty response")
            return False

    except Exception as e:
        print(f"❌ LLM function test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=== LLM Service Test ===\n")

    tests = [
        test_ollama_status,
        test_llm_function,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n=== Test Results: {passed}/{total} tests passed ===")

    if passed == total:
        print("✅ All tests passed! LLM service is ready.")
    else:
        print("❌ Some tests failed. Check Ollama setup.")


if __name__ == '__main__':
    main()