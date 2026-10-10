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
    Gate(
        "ai_provider_e2e",
        ("GEMINI_API_KEY", "OPENROUTER_API_KEY", "MISTRAL_API_KEY", "COHERE_API_KEY", "GROQ_API_KEY", "VOYAGE_API_KEY", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"),
        ("COGNIX_AI_BASE_URL", "COGNIX_AI_MODEL", "COGNIX_LLM_API_KEY", "COGNIX_LLM_API_URL", "COGNIX_LLM_MODEL"),
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
    Gate("database_recovery", ("DATABASE_URL", "COGNIX_RECOVERY_TARGET_DATABASE_URL")),
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
    }
    any_selected = any(selected.values())
    provider_gates = {"ai_provider_e2e", "supabase_storage", "backblaze_b2", "google_drive", "cloudinary", "production_database"}
    group_by_gate = {
        **{name: "provider" for name in provider_gates},
        "production_database": "provider",
        "database_recovery": "recovery",
        "authenticated_browser": "browser",
        "sentry": "sentry",
    }
    if selected["book"]:
        provider_gates = provider_gates | {"production_database"}
        group_by_gate["production_database"] = "book"
    active_gates = [
        gate
        for gate in GATES
        if not any_selected or group_by_gate.get(gate.name) in {
            key for key, value in selected.items() if value
        }
    ]
    for gate in active_gates:
        missing = [key for key in gate.required if not present(key)]
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
