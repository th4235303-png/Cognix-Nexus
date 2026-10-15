from __future__ import annotations

"""Lighthouse performance/accessibility baseline check.

Runs `npx lighthouse` against the frontend URL and reports:
  - Performance score
  - Accessibility score
  - Best-practices score
  - SEO score

Fails if:
  - accessibility < 0.9
  - performance < 0.5

Saves the full Lighthouse JSON report to test-results/lighthouse-report.json.

Usage:
  python scripts/lighthouse_check.py --url https://example.com
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


REPORT_DIR = Path("test-results")
REPORT_PATH = REPORT_DIR / "lighthouse-report.json"

FAIL_THRESHOLDS = {
    "accessibility": 0.9,
    "performance": 0.5,
}


def run_lighthouse(url: str, output_path: Path, timeout: int) -> dict:
    """Run npx lighthouse and return the parsed JSON report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "npx",
        "--yes",
        "lighthouse",
        url,
        "--output=json",
        f"--output-path={output_path}",
        "--chrome-flags=--headless --no-sandbox --disable-dev-shm-usage",
        "--quiet",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"lighthouse timed out after {timeout}s")
    except FileNotFoundError:
        raise RuntimeError(
            "npx not found. Node.js must be installed and npx must be on PATH."
        )

    if result.returncode not in (0, 1):
        # Lighthouse exits 1 when audits fail thresholds but report is still valid.
        # Non-zero other than 0/1 generally means a startup/chrome issue.
        stderr_preview = (result.stderr or "")[:500]
        raise RuntimeError(
            f"lighthouse exited with code {result.returncode}: {stderr_preview}"
        )

    if not output_path.exists():
        raise RuntimeError(
            f"lighthouse did not produce output at {output_path}. "
            f"stderr: {(result.stderr or '')[:500]}"
        )

    with output_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def extract_scores(report: dict) -> dict[str, float | None]:
    """Extract category scores from a Lighthouse report."""
    categories = report.get("categories", {})
    return {
        "performance": categories.get("performance", {}).get("score"),
        "accessibility": categories.get("accessibility", {}).get("score"),
        "best-practices": categories.get("best-practices", {}).get("score"),
        "seo": categories.get("seo", {}).get("score"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Lighthouse performance/accessibility baseline")
    parser.add_argument(
        "--url",
        default=os.getenv("COGNIX_E2E_BASE_URL", "").strip(),
        help="Frontend URL to audit (defaults to COGNIX_E2E_BASE_URL env var)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Subprocess timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "--output",
        default=str(REPORT_PATH),
        help=f"Path to write the Lighthouse JSON report (default: {REPORT_PATH})",
    )
    args = parser.parse_args()

    url = args.url
    if not url:
        result = {
            "status": "ERROR",
            "error": "--url argument or COGNIX_E2E_BASE_URL env var is required",
        }
        print(json.dumps(result, indent=2))
        return 1

    output_path = Path(args.output)

    try:
        report = run_lighthouse(url, output_path, args.timeout)
    except Exception as exc:
        result = {
            "status": "ERROR",
            "error": str(exc),
            "url": url,
        }
        print(json.dumps(result, indent=2))
        return 1

    scores = extract_scores(report)

    failures = []
    for metric, threshold in FAIL_THRESHOLDS.items():
        score = scores.get(metric)
        if score is None:
            failures.append(f"{metric}: score not available in report")
        elif score < threshold:
            failures.append(
                f"{metric}: {score:.2f} < threshold {threshold:.2f}"
            )

    overall_ok = len(failures) == 0
    result = {
        "status": "PASS" if overall_ok else "FAIL",
        "url": url,
        "scores": scores,
        "thresholds": FAIL_THRESHOLDS,
        "failures": failures,
        "report_path": str(output_path.resolve()),
    }

    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
