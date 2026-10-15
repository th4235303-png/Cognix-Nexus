#!/usr/bin/env python3
"""Safe PostgreSQL backup/restore drill helper.

This script never restores into a target database unless --allow-restore is
explicitly supplied. Production backups should be encrypted by the platform
backup/KMS layer; this helper verifies dump integrity and exercises restore
against an isolated target supplied by the operator.
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


def run_backup(source_dsn: str, output: Path) -> str:
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["pg_dump", "--format=custom", "--no-owner", "--no-acl", source_dsn, "--file", str(output)],
        check=True,
    )
    return sha256_file(output)


def run_restore(target_dsn: str, dump: Path) -> None:
    if not os.getenv("COGNIX_ALLOW_RESTORE", "").strip().lower() == "true":
        raise SystemExit("Restore blocked: set COGNIX_ALLOW_RESTORE=true for an explicit isolated restore drill")
    subprocess.run(
        ["pg_restore", "--exit-on-error", "--no-owner", "--no-acl", "--dbname", target_dsn, str(dump)],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", type=Path)
    parser.add_argument("--source-dsn", default=os.getenv("DATABASE_URL", ""))
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--restore", type=Path)
    parser.add_argument("--target-dsn", default="")
    parser.add_argument("--allow-restore", action="store_true")
    args = parser.parse_args()

    if args.dump:
        if not args.source_dsn:
            raise SystemExit("--source-dsn or DATABASE_URL is required")
        checksum = run_backup(args.source_dsn, args.dump)
        print(checksum)
        return

    if args.verify:
        print(sha256_file(args.verify))
        return

    if args.restore:
        if not args.target_dsn:
            raise SystemExit("--target-dsn is required for restore")
        if not args.allow_restore:
            raise SystemExit("Pass --allow-restore and set COGNIX_ALLOW_RESTORE=true")
        run_restore(args.target_dsn, args.restore)
        print("restore-complete")
        return

    parser.error("Choose --dump, --verify, or --restore")


if __name__ == "__main__":
    main()
