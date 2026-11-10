#!/usr/bin/env python3
"""Safe PostgreSQL backup/restore drill helper.

Restores are deliberately fail-closed: they require an explicit isolation
assertion, a target DSN distinct from the source DSN, and an explicit CLI opt-in.
The helper never prints DSNs or secret values.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_archive(dump: Path, expected_sha256: str = "") -> str:
    if not dump.is_file() or dump.stat().st_size == 0:
        raise SystemExit("Backup verification failed: dump is missing or empty")
    actual = sha256_file(dump)
    if expected_sha256 and actual.lower() != expected_sha256.strip().lower():
        raise SystemExit("Backup verification failed: SHA-256 does not match the recorded checksum")
    # A matching checksum only proves byte identity. Ask pg_restore to parse
    # the archive too, so truncated/non-PostgreSQL files cannot pass preflight.
    subprocess.run(
        ["pg_restore", "--list", str(dump)],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return actual


def run_backup(source_dsn: str, output: Path) -> str:
    if not source_dsn.strip():
        raise SystemExit("A source database DSN is required")
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["pg_dump", "--format=custom", "--no-owner", "--no-acl", source_dsn, "--file", str(output)],
        check=True,
    )
    return verify_archive(output)


def run_restore(
    target_dsn: str,
    dump: Path,
    *,
    source_dsn: str,
    isolated: str,
    allow_restore: bool,
    expected_sha256: str = "",
) -> str:
    if not allow_restore or os.getenv("COGNIX_ALLOW_RESTORE", "").strip().lower() != "true":
        raise SystemExit("Restore blocked: explicit CLI and COGNIX_ALLOW_RESTORE=true approvals are required")
    if isolated.strip().lower() != "true":
        raise SystemExit("Restore blocked: COGNIX_RECOVERY_TARGET_ISOLATED must be explicitly true")
    if not source_dsn.strip() or not target_dsn.strip():
        raise SystemExit("Restore blocked: source and target DSNs are both required")
    if source_dsn.strip() == target_dsn.strip():
        raise SystemExit("Restore blocked: source and recovery target DSNs must differ")
    checksum = verify_archive(dump, expected_sha256)
    subprocess.run(
        ["pg_restore", "--exit-on-error", "--no-owner", "--no-acl", "--dbname", target_dsn, str(dump)],
        check=True,
    )
    return checksum


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", type=Path)
    parser.add_argument("--source-dsn", default=os.getenv("DATABASE_URL", ""))
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--expected-sha256", default="")
    parser.add_argument("--restore", type=Path)
    parser.add_argument("--target-dsn", default="")
    parser.add_argument("--isolated", default=os.getenv("COGNIX_RECOVERY_TARGET_ISOLATED", ""))
    parser.add_argument("--allow-restore", action="store_true")
    args = parser.parse_args()

    if args.dump:
        checksum = run_backup(args.source_dsn, args.dump)
        print(checksum)
        return

    if args.verify:
        print(verify_archive(args.verify, args.expected_sha256))
        return

    if args.restore:
        checksum = run_restore(
            args.target_dsn,
            args.restore,
            source_dsn=args.source_dsn,
            isolated=args.isolated,
            allow_restore=args.allow_restore,
            expected_sha256=args.expected_sha256,
        )
        print(f"restore-complete sha256={checksum}")
        return

    parser.error("Choose --dump, --verify, or --restore")


if __name__ == "__main__":
    main()
