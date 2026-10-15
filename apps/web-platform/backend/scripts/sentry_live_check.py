from __future__ import annotations

"""Explicit opt-in Sentry ingestion probe.

Sends one non-sensitive test event and flushes the SDK. A successful flush is
evidence that the SDK accepted the event locally; UI observation remains a
separate operator gate.
"""

import json
import os
import sentry_sdk


def main() -> int:
    dsn = os.getenv("SENTRY_DSN", "").strip()
    if not dsn:
        print(json.dumps({"status": "NOT_RUN", "missing": ["SENTRY_DSN"]}))
        return 1
    sentry_sdk.init(
        dsn=dsn,
        environment=os.getenv("SENTRY_ENVIRONMENT", "production"),
        traces_sample_rate=0.0,
        send_default_pii=False,
    )
    event_id = sentry_sdk.capture_message("Cognix Nexus release-gate Sentry ingestion probe", level="info")
    sentry_sdk.flush(timeout=10)
    sentry_sdk.close()
    print(json.dumps({
        "status": "FLUSHED",
        "event_label": "cognix-release-gate-probe",
        "event_id": event_id,
        "secret_values_printed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
