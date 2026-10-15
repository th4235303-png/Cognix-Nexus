from __future__ import annotations

"""Read-only release-gate preflight.

This command never prints secret values. It reports which external gates are
runnable from the current environment and which required variables are missing.
It is intentionally separate from the real drills: a green preflight is not a
production PASS.
"""

import json
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Gate:
    name: str
    required: tuple[str, ...]
    optional: tuple[str, ...] = ()


GATES = (
    # The persisted vector schema is vector(1536), so Cohere is currently
    # the only configured embedding route compatible with production data.
    # Other LLM providers are optional and automatically join routing when keyed.
    Gate(
        "ai_provider_e2e",
        ("COHERE_API_KEY",),
        ("GEMINI_API_KEY", "OPENROUTER_API_KEY", "HUGGINGFACE_API_KEY", "MISTRAL_API_KEY", "GROQ_API_KEY", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID", "VOYAGE_API_KEY"),
    ),
    Gate("supabase_storage", ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "COGNIX_SUPABASE_STORAGE_BUCKET")),
    Gate("backblaze_b2", ("COGNIX_B2_ENDPOINT", "COGNIX_B2_BUCKET", "COGNIX_B2_KEY_ID", "COGNIX_B2_APPLICATION_KEY")),
    Gate(
        "google_drive",
        ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI", "GOOGLE_REFRESH_TOKEN"),
        ("GOOGLE_DRIVE_ROOT_FOLDER_ID",),
    ),
    Gate("cloudinary", ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")),
    Gate("sentry", ("SENTRY_DSN",)),
    Gate("authenticated_browser", ("COGNIX_E2E_BASE_URL", "COGNIX_E2E_API_URL", "COGNIX_E2E_EMAIL", "COGNIX_E2E_PASSWORD")),
    Gate("production_database", ("DATABASE_URL",)),
    # Synthetic Book fixtures must never be written to the production database.
    Gate("book_acceptance_database", ("COGNIX_BOOK_ACCEPTANCE_DATABASE_URL",)),
    Gate("database_recovery", ("DATABASE_URL", "COGNIX_RECOVERY_TARGET_DATABASE_URL", "COGNIX_RECOVERY_TARGET_ISOLATED")),
    Gate("render_health", ("COGNIX_API_BASE_URL",)),
)


def present(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def main() -> int:
    gates = []
    selected = {
        "provider": os.getenv("COGNIX_RUN_PROVIDER_E2E", "").strip().lower() == "true",
        "book": os.getenv("COGNIX_RUN_BOOK_CONTRACT", "").strip().lower() == "true",
        "browser": os.getenv("COGNIX_RUN_BROWSER_SMOKE", "").strip().lower() == "true",
        "sentry": os.getenv("COGNIX_RUN_SENTRY_PROBE", "").strip().lower() == "true",
        "recovery": os.getenv("COGNIX_RUN_RECOVERY", "").strip().lower() == "true",
        "render": os.getenv("COGNIX_RUN_RENDER_HEALTH", "").strip().lower() == "true",
    }
    any_selected = any(selected.values())
    group_by_gate = {
        "ai_provider_e2e": "provider",
        "supabase_storage": "provider",
        "backblaze_b2": "provider",
        "google_drive": "provider",
        "cloudinary": "provider",
        "production_database": "provider",
        "book_acceptance_database": "book",
        "database_recovery": "recovery",
        "authenticated_browser": "browser",
        "sentry": "sentry",
        "render_health": "render",
    }
    active_groups = {key for key, value in selected.items() if value}
    active_gates = [
        gate
        for gate in GATES
        if not any_selected or group_by_gate.get(gate.name) in active_groups
    ]
    for gate in active_gates:
        missing = [key for key in gate.required if not present(key)]
        if gate.name == "database_recovery":
            if present("DATABASE_URL") and present("COGNIX_RECOVERY_TARGET_DATABASE_URL"):
                if os.getenv("DATABASE_URL", "").strip() == os.getenv("COGNIX_RECOVERY_TARGET_DATABASE_URL", "").strip():
                    missing.append("COGNIX_RECOVERY_TARGET_DATABASE_URL must differ from DATABASE_URL")
            if present("COGNIX_RECOVERY_TARGET_ISOLATED") and os.getenv("COGNIX_RECOVERY_TARGET_ISOLATED", "").strip().lower() != "true":
                missing.append("COGNIX_RECOVERY_TARGET_ISOLATED must be explicitly set to true")
        optional_missing = [key for key in gate.optional if not present(key)]
        gates.append(
            {
                "gate": gate.name,
                "runnable": not missing,
                "missing_required": missing,
                "missing_optional": optional_missing,
            }
        )

    result = {
        "preflight": "READY" if all(g["runnable"] for g in gates) else "PARTIAL",
        "secret_values_printed": False,
        "gates": gates,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    # Fail fast only for explicitly selected gates. With no selection this is
    # an informational inventory and must not block the default workflow run.
    return 1 if any_selected and any(not gate["runnable"] for gate in gates) else 0


if __name__ == "__main__":
    raise SystemExit(main())
