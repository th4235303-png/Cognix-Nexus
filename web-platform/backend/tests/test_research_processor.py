import os
import unittest
from unittest.mock import Mock, patch

from app.services.research_processor import _wikipedia_core_api_url, _wikipedia_rest_url, clean_text, fetch_source, mock_key_points, mock_summary, process_stage


class ResearchProcessorTests(unittest.TestCase):
    def test_clean_text_normalizes_whitespace(self):
        self.assertEqual(clean_text("  Hello   world\n\n  Second line "), "Hello world\nSecond line")

    def test_mock_summary_and_key_points_are_deterministic(self):
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."
        self.assertEqual(mock_summary(text), "First sentence. Second sentence! Third sentence?")
        self.assertEqual(mock_key_points(text), ["First sentence.", "Second sentence!", "Third sentence?", "Fourth sentence."])

    def test_wikipedia_urls_use_public_rest_fallback(self):
        self.assertEqual(
            _wikipedia_rest_url("https://en.wikipedia.org/wiki/Logistics"),
            "https://en.wikipedia.org/api/rest_v1/page/html/Logistics",
        )
        self.assertIsNone(_wikipedia_rest_url("https://example.com/wiki/Logistics"))

    def test_wikipedia_core_api_fallback_url(self):
        self.assertEqual(
            _wikipedia_core_api_url("https://en.wikipedia.org/wiki/Logistics"),
            ("https://api.wikimedia.org", "en", "Logistics"),
        )
        self.assertIsNone(_wikipedia_core_api_url("https://example.com/wiki/Logistics"))

    def test_mock_processing_creates_translation_and_key_points(self):
        source = {"url": "https://example.com", "ai_summary": "A short summary."}
        with patch.dict(os.environ, {"COGNIX_PROCESSING_PROVIDER": "mock"}):
            translation = process_stage("translating", source)
            points = process_stage("key_points", source)
        self.assertEqual(translation.translation, "A short summary.")
        self.assertEqual(points.key_points, ["A short summary."])


if __name__ == "__main__":
    unittest.main()


def _response(status: int, text: str = "ok", headers: dict | None = None):
    item = Mock()
    item.status_code = status
    item.text = text
    item.content = text.encode()
    item.headers = headers or {"content-type": "text/plain"}
    item.is_redirect = False
    item.raise_for_status.side_effect = None
    return item


class SourceFetchRetryTests(unittest.TestCase):
    @patch("app.services.research_processor.time.sleep")
    @patch("app.services.research_processor.httpx.Client")
    @patch("app.services.research_processor._assert_public_url")
    def test_retries_rate_limit_then_succeeds(self, assert_public_url, client_cls, sleep):
        client = client_cls.return_value.__enter__.return_value
        client.get.side_effect = [
            _response(429, headers={"content-type": "text/plain", "retry-after": "0"}),
            _response(200, "retry success"),
        ]
        self.assertEqual(fetch_source("https://example.com/test"), "retry success")
        self.assertEqual(client.get.call_count, 2)
        sleep.assert_called_once()

    @patch("app.services.research_processor.time.sleep")
    @patch("app.services.research_processor.httpx.Client")
    @patch("app.services.research_processor._assert_public_url")
    def test_retries_server_error_then_succeeds(self, assert_public_url, client_cls, sleep):
        client = client_cls.return_value.__enter__.return_value
        client.get.side_effect = [_response(503), _response(200, "server recovered")]
        self.assertEqual(fetch_source("https://example.com/test"), "server recovered")
        self.assertEqual(client.get.call_count, 2)
        sleep.assert_called_once()

    @patch("app.services.research_processor.time.sleep")
    @patch("app.services.research_processor.httpx.Client")
    @patch("app.services.research_processor._assert_public_url")
    def test_timeout_is_retried(self, assert_public_url, client_cls, sleep):
        import httpx

        client = client_cls.return_value.__enter__.return_value
        client.get.side_effect = [httpx.ReadTimeout("temporary timeout"), _response(200, "timeout recovered")]
        self.assertEqual(fetch_source("https://example.com/test"), "timeout recovered")
        self.assertEqual(client.get.call_count, 2)
        sleep.assert_called_once()
