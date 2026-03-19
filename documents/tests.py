import json
from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings


LLM_SETTINGS = dict(
    LLM_BASE_URL='http://testserver',
    LLM_MODEL='phi4',
    LLM_TIMEOUT_SECONDS=10,
)


class SummarizeWithAITests(TestCase):
    """Unit tests for summarize_with_ai().

    All tests mock httpx.Client so no real network call is made.
    Use @override_settings to inject predictable LLM_* values.
    """

    def _make_mock_client(self, status_code: int, content: str):
        """Return a mock httpx.Client context manager whose .post() returns the given response."""
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.text = content
        mock_response.json.return_value = {
            "choices": [{"message": {"content": content}}]
        }

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        return mock_client

    @override_settings(**LLM_SETTINGS)
    @patch('documents.tasks.httpx.Client')
    def test_happy_path_returns_analysis_result(self, mock_client_cls):
        """Valid JSON response is parsed into an AnalysisResult."""
        valid_payload = json.dumps({
            "summary": "This document covers AI integration.",
            "key_points": ["Point one", "Point two"],
            "topics": ["AI", "Django"],
        })
        mock_client_cls.return_value = self._make_mock_client(200, valid_payload)

        from documents.tasks import summarize_with_ai
        result = summarize_with_ai(document_id=1, text="Test document text")

        self.assertEqual(result.summary, "This document covers AI integration.")
        self.assertEqual(result.key_points, ["Point one", "Point two"])
        self.assertEqual(result.topics, ["AI", "Django"])

    @override_settings(**LLM_SETTINGS)
    @patch('documents.tasks.httpx.Client')
    def test_non_200_response_raises_runtime_error(self, mock_client_cls):
        """HTTP error from LLM endpoint raises RuntimeError so Celery can retry."""
        mock_client_cls.return_value = self._make_mock_client(503, "Service Unavailable")

        from documents.tasks import summarize_with_ai
        with self.assertRaises(RuntimeError) as ctx:
            summarize_with_ai(document_id=1, text="some text")

        self.assertIn("503", str(ctx.exception))

    @override_settings(**LLM_SETTINGS)
    @patch('documents.tasks.httpx.Client')
    def test_invalid_json_response_raises_runtime_error(self, mock_client_cls):
        """Non-JSON response from LLM raises RuntimeError."""
        mock_client_cls.return_value = self._make_mock_client(200, "not json at all")

        from documents.tasks import summarize_with_ai
        with self.assertRaises(RuntimeError) as ctx:
            summarize_with_ai(document_id=1, text="some text")

        self.assertIn("not valid JSON", str(ctx.exception))

    @override_settings(**LLM_SETTINGS)
    @patch('documents.tasks.httpx.Client')
    def test_valid_json_wrong_schema_raises_runtime_error(self, mock_client_cls):
        """JSON with wrong keys fails Pydantic validation and raises RuntimeError."""
        wrong_schema = json.dumps({"unexpected_key": "value"})
        mock_client_cls.return_value = self._make_mock_client(200, wrong_schema)

        from documents.tasks import summarize_with_ai
        with self.assertRaises(RuntimeError) as ctx:
            summarize_with_ai(document_id=1, text="some text")

        self.assertIn("schema validation", str(ctx.exception))
