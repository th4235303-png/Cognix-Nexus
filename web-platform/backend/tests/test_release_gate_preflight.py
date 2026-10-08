import io
import json
import os
import unittest
from contextlib import redirect_stdout

from scripts.release_gate_preflight import main


class ReleaseGatePreflightTests(unittest.TestCase):
    def setUp(self):
        self.original = dict(os.environ)
        for key in {
            "COGNIX_AI_API_KEY", "COGNIX_EMBEDDING_API_KEY", "CLOUDFLARE_ACCOUNT_ID",
            "COGNIX_EMBEDDING_API_URL", "COGNIX_EMBEDDING_MODEL",
            "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY",
            "COGNIX_SUPABASE_STORAGE_BUCKET", "COGNIX_B2_ENDPOINT",
            "COGNIX_B2_BUCKET", "COGNIX_B2_KEY_ID", "COGNIX_B2_APPLICATION_KEY", "CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET",
            "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI", "GOOGLE_REFRESH_TOKEN",
            "SENTRY_DSN", "COGNIX_E2E_BASE_URL", "COGNIX_E2E_EMAIL",
            "COGNIX_E2E_PASSWORD", "DATABASE_URL", "COGNIX_RECOVERY_TARGET_DATABASE_URL",
        }:
            os.environ.pop(key, None)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.original)

    def test_preflight_never_prints_secret_values(self):
        os.environ["SENTRY_DSN"] = "super-secret-dsn"
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(), 0)
        payload = json.loads(out.getvalue())
        self.assertFalse(payload["secret_values_printed"])
        self.assertNotIn("super-secret-dsn", out.getvalue())

    def test_all_required_gates_become_runnable(self):
        os.environ.update({
            "COGNIX_AI_API_KEY": "ai",
            "COGNIX_EMBEDDING_API_KEY": "embed",
            "COGNIX_EMBEDDING_API_URL": "https://example.invalid/embed",
            "COGNIX_EMBEDDING_MODEL": "model",
            "SUPABASE_URL": "https://example.invalid",
            "SUPABASE_SERVICE_ROLE_KEY": "supabase",
            "COGNIX_SUPABASE_STORAGE_BUCKET": "bucket",
            "COGNIX_B2_ENDPOINT": "https://example.invalid",
            "COGNIX_B2_BUCKET": "bucket",
            "COGNIX_B2_KEY_ID": "key",
            "COGNIX_B2_APPLICATION_KEY": "secret",
            "CLOUDINARY_CLOUD_NAME": "cloud",
            "CLOUDINARY_API_KEY": "cloud-key",
            "CLOUDINARY_API_SECRET": "cloud-secret",
            "GOOGLE_CLIENT_ID": "client",
            "GOOGLE_CLIENT_SECRET": "secret",
            "GOOGLE_REDIRECT_URI": "https://example.invalid/callback",
            "GOOGLE_REFRESH_TOKEN": "refresh",
            "SENTRY_DSN": "https://example.invalid/1",
            "COGNIX_E2E_BASE_URL": "https://example.invalid",
            "COGNIX_E2E_API_URL": "https://api.example.invalid",
            "COGNIX_E2E_EMAIL": "e2e@example.invalid",
            "COGNIX_E2E_PASSWORD": "password",
            "GEMINI_API_KEY": "gemini",
            "OPENROUTER_API_KEY": "openrouter",
            "HUGGINGFACE_API_KEY": "huggingface",
            "CEREBRAS_API_KEY": "cerebras",
            "MISTRAL_API_KEY": "mistral",
            "COHERE_API_KEY": "cohere",
            "GROQ_API_KEY": "groq",
            "VOYAGE_API_KEY": "voyage",
            "CLOUDFLARE_API_TOKEN": "cloudflare",
            "CLOUDFLARE_ACCOUNT_ID": "account",
            "DATABASE_URL": "postgresql://example.invalid/db",
            "COGNIX_RECOVERY_TARGET_DATABASE_URL": "postgresql://example.invalid/recovery",
        })
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(), 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["preflight"], "READY")
        self.assertTrue(all(g["runnable"] for g in payload["gates"]))

    def test_recovery_target_is_only_required_when_recovery_is_selected(self):
        os.environ["DATABASE_URL"] = "postgresql://example.invalid/db"
        os.environ["COGNIX_RUN_PROVIDER_E2E"] = "true"
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(), 0)
        payload = json.loads(out.getvalue())
        self.assertNotIn("database_recovery", {g["gate"] for g in payload["gates"]})

        os.environ["COGNIX_RUN_RECOVERY"] = "true"
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(), 0)
        payload = json.loads(out.getvalue())
        recovery = next(g for g in payload["gates"] if g["gate"] == "database_recovery")
        self.assertEqual(recovery["missing_required"], ["COGNIX_RECOVERY_TARGET_DATABASE_URL"])


if __name__ == "__main__":
    unittest.main()
