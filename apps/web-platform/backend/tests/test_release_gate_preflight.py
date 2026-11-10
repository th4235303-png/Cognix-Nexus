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
            "CLOUDFLARE_ACCOUNT_ID",
            "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY",
            "COGNIX_SUPABASE_STORAGE_BUCKET", "COGNIX_B2_ENDPOINT",
            "COGNIX_B2_BUCKET", "COGNIX_B2_KEY_ID", "COGNIX_B2_APPLICATION_KEY", "CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET",
            "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI", "GOOGLE_REFRESH_TOKEN",
            "SENTRY_DSN", "COGNIX_E2E_BASE_URL", "COGNIX_E2E_API_URL", "COGNIX_E2E_EMAIL",
            "COGNIX_E2E_PASSWORD", "DATABASE_URL", "COGNIX_BOOK_ACCEPTANCE_DATABASE_URL",
            "COGNIX_RECOVERY_TARGET_DATABASE_URL", "COGNIX_RECOVERY_TARGET_ISOLATED",
            "COGNIX_RUN_PROVIDER_E2E", "COGNIX_RUN_BOOK_CONTRACT", "COGNIX_RUN_BROWSER_SMOKE",
            "COGNIX_RUN_SENTRY_PROBE", "COGNIX_RUN_RECOVERY", "COGNIX_API_BASE_URL",
            "COGNIX_WORKER_BASE_URL",
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
            "MISTRAL_API_KEY": "mistral",
            "COHERE_API_KEY": "cohere",
            "GROQ_API_KEY": "groq",
            "VOYAGE_API_KEY": "voyage",
            "CLOUDFLARE_API_TOKEN": "cloudflare",
            "CLOUDFLARE_ACCOUNT_ID": "account",
            "DATABASE_URL": "postgresql://example.invalid/db",
            "COGNIX_BOOK_ACCEPTANCE_DATABASE_URL": "postgresql://example.invalid/book-test",
            "COGNIX_RECOVERY_TARGET_DATABASE_URL": "postgresql://example.invalid/recovery",
            "COGNIX_RECOVERY_TARGET_ISOLATED": "true",
            "COGNIX_API_BASE_URL": "https://api.example.invalid",
            "COGNIX_WORKER_BASE_URL": "https://worker.example.invalid",
        })
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(), 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["preflight"], "READY")
        self.assertTrue(all(g["runnable"] for g in payload["gates"]))

    def test_book_gate_does_not_require_production_database(self):
        os.environ.update({
            "COGNIX_RUN_BOOK_CONTRACT": "true",
            "COGNIX_BOOK_ACCEPTANCE_DATABASE_URL": "postgresql://example.invalid/book-test",
        })
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(), 0)
        payload = json.loads(out.getvalue())
        self.assertEqual([g["gate"] for g in payload["gates"]], ["book_acceptance_database"])
        self.assertTrue(payload["gates"][0]["runnable"])

    def test_recovery_target_is_only_required_when_recovery_is_selected(self):
        os.environ["DATABASE_URL"] = "postgresql://example.invalid/db"
        os.environ["COGNIX_RUN_PROVIDER_E2E"] = "true"
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(), 1)  # selected provider gate is incomplete
        payload = json.loads(out.getvalue())
        self.assertNotIn("database_recovery", {g["gate"] for g in payload["gates"]})

        os.environ.pop("COGNIX_RUN_PROVIDER_E2E", None)
        os.environ["COGNIX_RUN_RECOVERY"] = "true"
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(), 1)  # recovery target and isolation declaration are missing
        payload = json.loads(out.getvalue())
        recovery = next(g for g in payload["gates"] if g["gate"] == "database_recovery")
        self.assertEqual(
            recovery["missing_required"],
            ["COGNIX_RECOVERY_TARGET_DATABASE_URL", "COGNIX_RECOVERY_TARGET_ISOLATED"],
        )

    def test_recovery_rejects_same_source_and_target_dsn(self):
        os.environ.update({
            "DATABASE_URL": "postgresql://example.invalid/db",
            "COGNIX_RECOVERY_TARGET_DATABASE_URL": "postgresql://example.invalid/db",
            "COGNIX_RECOVERY_TARGET_ISOLATED": "true",
            "COGNIX_RUN_RECOVERY": "true",
        })
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(), 1)
        payload = json.loads(out.getvalue())
        recovery = next(g for g in payload["gates"] if g["gate"] == "database_recovery")
        self.assertIn("COGNIX_RECOVERY_TARGET_DATABASE_URL must differ from DATABASE_URL", recovery["missing_required"])

    def test_recovery_requires_explicit_isolation_true(self):
        os.environ.update({
            "DATABASE_URL": "postgresql://example.invalid/db",
            "COGNIX_RECOVERY_TARGET_DATABASE_URL": "postgresql://example.invalid/recovery",
            "COGNIX_RECOVERY_TARGET_ISOLATED": "false",
            "COGNIX_RUN_RECOVERY": "true",
        })
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(main(), 1)
        payload = json.loads(out.getvalue())
        recovery = next(g for g in payload["gates"] if g["gate"] == "database_recovery")
        self.assertIn("COGNIX_RECOVERY_TARGET_ISOLATED must be explicitly set to true", recovery["missing_required"])




class BackupRestoreDrillSafetyTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.dump = Path(self.tempdir.name) / "backup.dump"
        self.dump.write_bytes(b"synthetic-postgres-custom-archive")
        self.patch = patch("scripts.backup_restore_drill.subprocess.run")
        self.run = self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_restore_requires_explicit_isolation(self):
        from scripts.backup_restore_drill import run_restore

        with self.assertRaisesRegex(SystemExit, "ISOLATED must be explicitly true"):
            run_restore(
                "postgresql://recovery/db",
                self.dump,
                source_dsn="postgresql://production/db",
                isolated="false",
                allow_restore=True,
            )
        self.run.assert_not_called()

    def test_restore_rejects_source_target_match(self):
        from scripts.backup_restore_drill import run_restore

        with self.assertRaisesRegex(SystemExit, "DSNs must differ"):
            run_restore(
                "postgresql://production/db",
                self.dump,
                source_dsn="postgresql://production/db",
                isolated="true",
                allow_restore=True,
            )
        self.run.assert_not_called()

    def test_restore_requires_both_explicit_approvals(self):
        from scripts.backup_restore_drill import run_restore

        with self.assertRaisesRegex(SystemExit, "explicit CLI and COGNIX_ALLOW_RESTORE"):
            run_restore(
                "postgresql://recovery/db",
                self.dump,
                source_dsn="postgresql://production/db",
                isolated="true",
                allow_restore=False,
            )
        self.run.assert_not_called()

    def test_checksum_mismatch_blocks_restore(self):
        import os
        from scripts.backup_restore_drill import run_restore

        os.environ["COGNIX_ALLOW_RESTORE"] = "true"
        self.addCleanup(os.environ.pop, "COGNIX_ALLOW_RESTORE", None)
        with self.assertRaisesRegex(SystemExit, "SHA-256 does not match"):
            run_restore(
                "postgresql://recovery/db",
                self.dump,
                source_dsn="postgresql://production/db",
                isolated="true",
                allow_restore=True,
                expected_sha256="0" * 64,
            )
        self.run.assert_not_called()

    def test_restore_validates_archive_before_running_restore(self):
        import os
        from scripts.backup_restore_drill import run_restore, sha256_file

        os.environ["COGNIX_ALLOW_RESTORE"] = "true"
        self.addCleanup(os.environ.pop, "COGNIX_ALLOW_RESTORE", None)
        checksum = sha256_file(self.dump)
        self.assertEqual(
            run_restore(
                "postgresql://recovery/db",
                self.dump,
                source_dsn="postgresql://production/db",
                isolated="true",
                allow_restore=True,
                expected_sha256=checksum,
            ),
            checksum,
        )
        self.assertEqual(self.run.call_count, 2)
        self.assertEqual(self.run.call_args_list[0].args[0][:2], ["pg_restore", "--list"])
        self.assertEqual(self.run.call_args_list[1].args[0][0], "pg_restore")



if __name__ == "__main__":
    unittest.main()
