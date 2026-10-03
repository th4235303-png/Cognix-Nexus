import os
import unittest
from unittest.mock import patch

import httpx
from fastapi import Request

from app.auth import _decode_token, _http_get_with_retries, _verify_with_supabase, auth_required
from app.main import _cors_origins, global_exception_handler, validate_production_configuration, v1_app


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
        request = httpx.Request("GET", "https://example.test/auth/v1/user")
        response = httpx.Response(200, request=request, json={"id": "user-1"})
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

    def test_decode_hs256_token(self):
        import jwt
        with patch.dict(os.environ, {"COGNIX_JWT_SECRET": "test-secret", "COGNIX_JWT_ISSUER": "", "COGNIX_JWT_AUDIENCE": ""}, clear=True):
            token = jwt.encode({"sub": "user-1"}, "test-secret", algorithm="HS256")
            claims = _decode_token(token)
        self.assertEqual(claims["sub"], "user-1")

    def test_decode_invalid_token_fails_closed(self):
        with patch.dict(os.environ, {"COGNIX_JWT_SECRET": "test-secret"}, clear=True):
            with self.assertRaises(Exception) as ctx:
                _decode_token("not-a-valid-token")
        self.assertEqual(getattr(ctx.exception, "status_code", None), 401)

    def test_supabase_auth_missing_configuration(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(Exception) as ctx:
                _verify_with_supabase("token")
        self.assertEqual(getattr(ctx.exception, "status_code", None), 503)

    def test_supabase_auth_success(self):
        request = httpx.Request("GET", "https://example.test/auth/v1/user")
        response = httpx.Response(200, request=request, json={"id": "user-2", "email": "user@example.test"})
        with patch.dict(os.environ, {"COGNIX_SUPABASE_URL": "https://example.test", "COGNIX_SUPABASE_PUBLISHABLE_KEY": "public"}, clear=True), patch("app.auth._http_get_with_retries", return_value=response):
            claims = _verify_with_supabase("token")
        self.assertEqual(claims["sub"], "user-2")
        self.assertEqual(claims["role"], "authenticated")

    def test_supabase_auth_rejects_401(self):
        request = httpx.Request("GET", "https://example.test/auth/v1/user")
        response = httpx.Response(401, request=request)
        with patch.dict(os.environ, {"COGNIX_SUPABASE_URL": "https://example.test", "COGNIX_SUPABASE_PUBLISHABLE_KEY": "public"}, clear=True), patch("app.auth._http_get_with_retries", return_value=response):
            with self.assertRaises(Exception) as ctx:
                _verify_with_supabase("token")
        self.assertEqual(getattr(ctx.exception, "status_code", None), 401)

    def test_production_cors_requires_exact_origin(self):
        with patch.dict(os.environ, {"COGNIX_ENV": "production", "COGNIX_CORS_ORIGINS": ""}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "COGNIX_CORS_ORIGINS"):
                _cors_origins()
        with patch.dict(os.environ, {"COGNIX_ENV": "production", "COGNIX_CORS_ORIGINS": "https://app.example"}, clear=True):
            self.assertEqual(_cors_origins(), ["https://app.example"])

    def test_versioned_openapi_surface_exists(self):
        schema = v1_app.openapi()
        self.assertEqual(schema["info"]["version"], "1.0.0")
        self.assertTrue(schema["paths"])


if __name__ == "__main__":
    unittest.main()
