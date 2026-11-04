"""Focused branch coverage for API bootstrap and middleware behavior."""
import asyncio
import unittest
from collections import defaultdict, deque
from unittest.mock import Mock, patch

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app import main


def make_request(path="/private", headers=None, query_string=b"", client=("test-client", 123)):
    return Request({
        "type": "http",
        "method": "GET",
        "path": path,
        "headers": headers or [],
        "query_string": query_string,
        "server": ("testserver", 80),
        "client": client,
        "scheme": "http",
    })


class MainCoverageTests(unittest.TestCase):
    def test_env_flag_normalizes_truthy_and_falsey_values(self):
        for value in ("1", "TRUE", " yes ", "On"):
            with self.subTest(value=value), patch.dict("os.environ", {"FLAG": value}):
                self.assertTrue(main._env_flag("FLAG"))
        with patch.dict("os.environ", {"FLAG": "disabled"}, clear=True):
            self.assertFalse(main._env_flag("FLAG"))
        with patch.dict("os.environ", {}, clear=True):
            self.assertTrue(main._env_flag("MISSING", "true"))

    def test_safe_request_path_redacts_secrets_and_bounds_path(self):
        request = make_request(
            "/x" * 260,
            query_string=b"token=abc&access_token=def&code=ghi&safe=value",
        )
        path = main._safe_request_path(request)
        self.assertLessEqual(len(path.split("?", 1)[0]), 500)
        self.assertIn("token=[REDACTED]", path)
        self.assertIn("access_token=[REDACTED]", path)
        self.assertIn("code=[REDACTED]", path)
        self.assertIn("safe=value", path)

    def test_cors_trims_trailing_slashes_and_ignores_empty_entries(self):
        with patch.dict("os.environ", {
            "COGNIX_ENV": "development",
            "COGNIX_CORS_ORIGINS": " https://one.example/ , ,https://two.example/// ",
        }, clear=True):
            self.assertEqual(
                main._cors_origins(),
                ["https://one.example", "https://two.example"],
            )

    def test_production_configuration_accepts_valid_configuration(self):
        with patch.dict("os.environ", {
            "COGNIX_ENV": "production",
            "DATABASE_URL": "postgresql://db.example/cognix",
            "COGNIX_AUTH_REQUIRED": "true",
            "COGNIX_DEV_MODE": "false",
            "COGNIX_CORS_ORIGINS": "https://app.example",
        }, clear=True):
            main.validate_production_configuration()

    def test_startup_initializes_database_and_tolerates_seed_failure(self):
        database = Mock()
        database.soul_seed_defaults.side_effect = RuntimeError("migration pending")
        with patch.object(main.store, "database", database), \
             patch.object(main.store, "initialize") as initialize, \
             patch.object(main, "validate_production_configuration"):
            main._startup()
        initialize.assert_called_once_with()
        database.soul_seed_defaults.assert_called_once_with()

    def test_startup_wraps_database_initialization_failure(self):
        database = Mock()
        with patch.object(main.store, "database", database), \
             patch.object(main.store, "initialize", side_effect=ValueError("db")), \
             patch.object(main, "validate_production_configuration"):
            with self.assertRaisesRegex(RuntimeError, "Failed to initialize database"):
                main._startup()

    def test_shutdown_closes_configured_database(self):
        database = Mock()
        with patch.object(main.store, "database", database):
            main._shutdown()
        database.close.assert_called_once_with()

    def test_root_and_health_payloads(self):
        self.assertEqual(main.root()["openapi"], "/v1/openapi.json")
        with patch.object(main, "DEPLOYMENT_REVISION", "revision-test"):
            self.assertEqual(main.health()["revision"], "revision-test")

    def test_readiness_without_database_when_database_optional(self):
        with patch.object(main.store, "database", None), \
             patch.object(main, "REQUIRE_DATABASE", False):
            result = main.readiness()
        self.assertEqual(result["persistence_mode"], "memory-prototype")
        self.assertEqual(result["status"], "ready")
        self.assertFalse(result["database_configured"])
        self.assertFalse(result["database_reachable"])

    def test_readiness_reports_unreachable_required_database(self):
        database = Mock()
        database.ping.return_value = False
        with patch.object(main.store, "database", database), \
             patch.object(main, "REQUIRE_DATABASE", True):
            result = main.readiness()
        self.assertEqual(result["status"], "not_ready")
        self.assertTrue(result["database_configured"])
        self.assertFalse(result["database_reachable"])

    def test_readiness_handles_database_ping_exception(self):
        database = Mock()
        database.ping.side_effect = OSError("offline")
        with patch.object(main.store, "database", database), \
             patch.object(main, "REQUIRE_DATABASE", False):
            result = main.readiness()
        self.assertEqual(result["status"], "not_ready")
        self.assertFalse(result["database_reachable"])

    def test_security_headers_are_added(self):
        async def call_next(_request):
            return JSONResponse({"ok": True})

        response = asyncio.run(main.security_headers(make_request(), call_next))
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertEqual(response.headers["x-frame-options"], "DENY")
        self.assertEqual(response.headers["referrer-policy"], "strict-origin-when-cross-origin")
        self.assertEqual(
            response.headers["permissions-policy"],
            "camera=(), microphone=(), geolocation=()",
        )

    def test_request_context_sets_request_id_and_resets_owner(self):
        async def call_next(_request):
            return JSONResponse({"ok": True})

        request = make_request(headers=[(b"x-request-id", b"request-test")])
        with patch.object(main, "authenticate_request", return_value={"sub": "owner-1"}), \
             patch.object(main, "set_request_owner", return_value="owner-token") as set_owner, \
             patch.object(main, "reset_request_owner") as reset_owner, \
             patch.object(main.store, "database", None):
            response = asyncio.run(main.request_context(request, call_next))
        self.assertEqual(response.headers["x-request-id"], "request-test")
        set_owner.assert_called_once_with("owner-1")
        reset_owner.assert_called_once_with("owner-token")

    def test_request_context_converts_http_exception_to_response(self):
        async def call_next(_request):
            raise HTTPException(status_code=403, detail="blocked")

        request = make_request()
        with patch.object(main, "authenticate_request", return_value={"sub": "owner-2"}), \
             patch.object(main, "set_request_owner", return_value="owner-token"), \
             patch.object(main, "reset_request_owner"), \
             patch.object(main.store, "database", None):
            response = asyncio.run(main.request_context(request, call_next))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.body, b'{"detail":"blocked"}')

    def test_rate_limit_prunes_expired_entries_and_bounds_identity_map(self):
        windows = defaultdict(deque)
        windows["stale"].append(1.0)
        async def call_next(_request):
            return JSONResponse({"ok": True})

        request = make_request(client=("new-client", 456))
        with patch.object(main, "RATE_LIMIT", 2), \
             patch.object(main, "RATE_LIMIT_MAX_IDENTITIES", 1), \
             patch.object(main, "_rate_windows", windows), \
             patch.object(main.time, "monotonic", return_value=100.0):
            response = asyncio.run(main.rate_limit(request, call_next))
        self.assertEqual(response.status_code, 200)
        self.assertIn("new-client", windows)
        self.assertNotIn("stale", windows)


if __name__ == "__main__":
    unittest.main()
