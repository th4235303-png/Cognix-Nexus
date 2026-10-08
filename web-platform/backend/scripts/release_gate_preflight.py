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
        ("COGNIX_AI_API_KEY", "COGNIX_EMBEDDING_API_KEY", "COGNIX_EMBEDDING_API_URL", "COGNIX_EMBEDDING_MODEL"),
        ("COGNIX_AI_BASE_URL", "COGNIX_AI_MODEL", "COGNIX_LLM_API_KEY", "COGNIX_LLM_API_URL", "COGNIX_LLM_MODEL"),
    ),
    Gate("supabase_storage", ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "COGNIX_SUPABASE_STORAGE_BUCKET")),
    Gate("backblaze_b2", ("COGNIX_B2_ENDPOINT", "COGNIX_B2_BUCKET", "COGNIX_B2_KEY_ID", "COGNIX_B2_APPLICATION_KEY")),
    Gate(
        "google_drive",
        ("GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI"),
        ("GOOGLE_REFRESH_TOKEN", "GOOGLE_DRIVE_ROOT_FOLDER_ID"),
    ),
    Gate("sentry", ("SENTRY_DSN",)),
    Gate("authenticated_browser", ("COGNIX_E2E_BASE_URL", "COGNIX_E2E_API_URL", "COGNIX_E2E_EMAIL", "COGNIX_E2E_PASSWORD")),
    Gate("database_recovery", ("DATABASE_URL",)),
)


def present(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def main() -> int:
    gates = []
    for gate in GATES:
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
