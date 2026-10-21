from __future__ import annotations

import io
import json
import unittest
from unittest import mock
import urllib.error

from scripts.render_health_check import fetch_endpoint


class RenderHealthCheckTests(unittest.TestCase):
    def test_retries_transient_timeout_then_passes(self):
        response = mock.MagicMock()
        response.__enter__.return_value.status = 200
        response.__enter__.return_value.read.return_value = b'{"status":"ok"}'
        with mock.patch(
            "scripts.render_health_check.urllib.request.urlopen",
            side_effect=[TimeoutError("read timed out"), response],
        ) as urlopen, mock.patch("scripts.render_health_check.time.sleep") as sleep:
            result = fetch_endpoint("https://example.invalid", "/health", 1, attempts=3, retry_delay=0.1)
        self.assertTrue(result["ok"])
        self.assertEqual(result["http_status"], 200)
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(0.1)

    def test_client_error_is_not_retried(self):
        error = urllib.error.HTTPError(
            "https://example.invalid/health", 401, "unauthorized", {}, None
        )
        with mock.patch(
            "scripts.render_health_check.urllib.request.urlopen", side_effect=error
        ) as urlopen, mock.patch("scripts.render_health_check.time.sleep") as sleep:
            result = fetch_endpoint("https://example.invalid", "/health", 1, attempts=3)
        self.assertFalse(result["ok"])
        self.assertEqual(result["http_status"], 401)
        self.assertEqual(result["attempts"], 1)
        urlopen.assert_called_once()
        sleep.assert_not_called()

    def test_server_error_is_retried(self):
        error = urllib.error.HTTPError(
            "https://example.invalid/health", 503, "unavailable", {}, None
        )
        response = mock.MagicMock()
        response.__enter__.return_value.status = 200
        response.__enter__.return_value.read.return_value = b'{"status":"ok"}'
        with mock.patch(
            "scripts.render_health_check.urllib.request.urlopen",
            side_effect=[error, response],
        ) as urlopen, mock.patch("scripts.render_health_check.time.sleep"):
            result = fetch_endpoint("https://example.invalid", "/health", 1, attempts=3)
        self.assertTrue(result["ok"])
        self.assertEqual(result["attempts"], 2)
        self.assertEqual(urlopen.call_count, 2)


if __name__ == "__main__":
    unittest.main()
