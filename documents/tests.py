import json
from unittest.mock import MagicMock, patch

from django.test import TestCase


class SummarizeWithAITests(TestCase):
    """Unit tests for summarize_with_ai().

    All tests mock the ask_llm function so no real network call is made.
    """

    @patch('documents.tasks.ask_llm')
    def test_happy_path_returns_analysis_result(self, mock_ask_llm):
        """Valid JSON response is parsed into an AnalysisResult."""
        valid_payload = json.dumps({
            "summary": "This document covers AI integration.",
            "key_points": ["Point one", "Point two"],
            "doc_type": "other",
        })
        mock_ask_llm.return_value = valid_payload

        from documents.tasks import summarize_with_ai
        result = summarize_with_ai(document_id=1, text="Test document text")

        self.assertEqual(result.summary, "This document covers AI integration.")
        self.assertEqual(result.key_points, ["Point one", "Point two"])
        self.assertEqual(result.doc_type, "other")

    @patch('documents.tasks.ask_llm')
    def test_invalid_json_response_raises_value_error(self, mock_ask_llm):
        """Non-JSON response from LLM raises ValueError."""
        mock_ask_llm.return_value = "not json at all"

        from documents.tasks import summarize_with_ai
        with self.assertRaises(ValueError) as ctx:
            summarize_with_ai(document_id=1, text="some text")

        self.assertIn("invalid JSON", str(ctx.exception))

    @patch('documents.tasks.ask_llm')
    def test_valid_json_wrong_schema_raises_value_error(self, mock_ask_llm):
        """JSON with wrong keys fails validation and raises ValueError."""
        wrong_schema = json.dumps({"unexpected_key": "value"})
        mock_ask_llm.return_value = wrong_schema

        from documents.tasks import summarize_with_ai
        with self.assertRaises(ValueError) as ctx:
            summarize_with_ai(document_id=1, text="some text")

        self.assertIn("missing required analysis fields", str(ctx.exception))

    @patch('documents.tasks.ask_llm')
    def test_doc_type_validation(self, mock_ask_llm):
        """Invalid doc_type is normalized to 'other'."""
        payload = json.dumps({
            "summary": "Test summary",
            "key_points": ["Point 1"],
            "doc_type": "invalid_type",
        })
        mock_ask_llm.return_value = payload

        from documents.tasks import summarize_with_ai
        result = summarize_with_ai(document_id=1, text="Test text")

        self.assertEqual(result.doc_type, "other")
