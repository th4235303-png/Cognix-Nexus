import os
import socket
import unittest
from unittest.mock import Mock, patch

from app.services.research_processor import _wikipedia_core_api_url, _wikipedia_rest_url, clean_text, fetch_source, mock_key_points, mock_summary, process_stage
from app.services.ssrf import UnsafeDestination


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



def _response(status: int, text: str = "ok", headers: dict | None = None):
    item = Mock()
    item.status_code = status
    item.text = text
    item.content = text.encode()
    item.headers = headers or {"content-type": "text/plain"}
    item.is_redirect = False
    item.raise_for_status.side_effect = None
    return item


def _redirect(location: str):
    response = _response(302, headers={"location": location})
    response.is_redirect = True
    return response


def _public_dns(_hostname, port, type):
    return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("93.184.216.34", port))]


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

    @patch("app.services.research_processor.httpx.Client")
    @patch("app.services.ssrf.socket.getaddrinfo", side_effect=[
        _public_dns("unused", 443, socket.SOCK_STREAM),
        [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("10.0.0.2", 443))],
    ])
    def test_redirect_to_private_address_is_rejected(self, getaddrinfo, client_cls):
        client = client_cls.return_value.__enter__.return_value
        client.get.return_value = _redirect("http://internal.example/private")
        with self.assertRaisesRegex(UnsafeDestination, "not public"):
            fetch_source("https://public.example/article")
        self.assertEqual(client.get.call_count, 1)

    @patch("app.services.research_processor.httpx.Client")
    def test_redirect_to_localhost_is_rejected(self, client_cls):
        client = client_cls.return_value.__enter__.return_value
        client.get.return_value = _redirect("http://localhost/private")
        with patch("app.services.ssrf.socket.getaddrinfo", side_effect=_public_dns):
            with self.assertRaises(UnsafeDestination):
                fetch_source("https://public.example/article")
        self.assertEqual(client.get.call_count, 1)

    @patch("app.services.research_processor.httpx.Client")
    @patch("app.services.ssrf.socket.getaddrinfo", side_effect=[
        _public_dns("unused", 443, socket.SOCK_STREAM),
        [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", ("127.0.0.1", 80))],
    ])
    def test_redirect_to_noncanonical_loopback_address_is_rejected(self, getaddrinfo, client_cls):
        client = client_cls.return_value.__enter__.return_value
        client.get.return_value = _redirect("http://2130706433/private")
        with self.assertRaises(UnsafeDestination):
            fetch_source("https://public.example/article")
        self.assertEqual(client.get.call_count, 1)

    @patch("app.services.research_processor.httpx.Client")
    def test_redirect_to_another_public_hostname_is_allowed(self, client_cls):
        client = client_cls.return_value.__enter__.return_value
        client.get.side_effect = [
            _redirect("https://other-public.example/article"),
            _response(200, "public redirect worked"),
        ]
        with patch("app.services.ssrf.socket.getaddrinfo", side_effect=_public_dns):
            self.assertEqual(
                fetch_source("https://public.example/start"),
                "public redirect worked",
            )
        self.assertEqual(client.get.call_count, 2)

    @patch("app.services.research_processor.time.sleep")
    @patch("app.services.research_processor.httpx.Client")
    def test_ssrf_rejection_from_transport_is_not_retried(self, client_cls, sleep):
        client = client_cls.return_value.__enter__.return_value
        client.get.side_effect = UnsafeDestination("Source destination is not public")
        with (
            patch("app.services.ssrf.socket.getaddrinfo", side_effect=_public_dns),
            self.assertRaises(UnsafeDestination),
        ):
            fetch_source("https://public.example/article")
        self.assertEqual(client.get.call_count, 1)
        sleep.assert_not_called()

    @patch("app.services.research_processor.httpx.Client")
    def test_wikipedia_403_still_uses_public_api_fallback(self, client_cls):
        client = client_cls.return_value.__enter__.return_value
        client.get.side_effect = [
            _response(403, "denied"),
            _response(200, "<html><body>Wikipedia fallback text</body></html>", {
                "content-type": "text/html",
            }),
        ]
        with patch("app.services.ssrf.socket.getaddrinfo", side_effect=_public_dns):
            self.assertEqual(
                fetch_source("https://en.wikipedia.org/wiki/Logistics"),
                "Wikipedia fallback text",
            )
        self.assertEqual(client.get.call_count, 2)


if __name__ == "__main__":
    unittest.main()
