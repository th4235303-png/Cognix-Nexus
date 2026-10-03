import os
import unittest
from unittest.mock import patch

import httpx
from fastapi import Request

from app.auth import _http_get_with_retries, auth_required
from app.main import global_exception_handler, validate_production_configuration


class SecurityHardeningTests(unittest.TestCase):
    def test_auth_is_fail_closed_by_default(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertTrue(auth_required())

    def test_dev_mode_explicitly_disables_auth(self):
        with patch.dict("os.environ", {"COGNIX_DEV_MODE": "true"}, clear=True):
            self.assertFalse(auth_required())

    def test_production_requires_database(self):
        with patch.dict(
            "os.environ",
            {"COGNIX_ENV": "production", "COGNIX_DEV_MODE": "false"},
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "DATABASE_URL must be set"):
                validate_production_configuration()

    def test_production_rejects_disabled_auth(self):
        with patch.dict(
            "os.environ",
            {
                "COGNIX_ENV": "production",
                "DATABASE_URL": "postgresql://example.invalid/db",
                "COGNIX_AUTH_REQUIRED": "false",
                "COGNIX_DEV_MODE": "false",
            },
            clear=True,
        ):
            with self.assertRaisesRegex(RuntimeError, "Authentication must be enabled"):
                validate_production_configuration()

    def test_auth_provider_retries_transient_failures(self):
        response = httpx.Response(200, json={"id": "user-1"})
        with patch("app.auth.httpx.get", side_effect=[httpx.ConnectError("temporary"), httpx.ConnectError("temporary"), response]) as get, patch("app.auth.time.sleep"):
            result = _http_get_with_retries("https://example.test/auth/v1/user", {"apikey": "publishable"}, attempts=3)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(get.call_count, 3)

    def test_auth_provider_does_not_retry_401(self):
        request = httpx.Request("GET", "https://example.test/auth/v1/user")
        response = httpx.Response(401, request=request)
        with patch("app.auth.httpx.get", return_value=response) as get:
            result = _http_get_with_retries("https://example.test/auth/v1/user", {"apikey": "publishable"}, attempts=3)
        self.assertEqual(result.status_code, 401)
        self.assertEqual(get.call_count, 1)

    def test_global_exception_handler_returns_safe_error(self):
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("testclient", 123),
            "scheme": "http",
        }
        request = Request(scope)
        response = __import__("asyncio").run(global_exception_handler(request, ValueError("secret-internal-detail")))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.body, b'{"detail":{"code":"INTERNAL_ERROR","message":"Internal server error"}}')


if __name__ == "__main__":
    unittest.main()
