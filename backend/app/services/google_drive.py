"""Google Drive integration boundary.

Production implementation should use OAuth 2.0 credentials from a backend
secret manager. The prototype intentionally returns mock state and never
accepts credentials from the browser.
"""

from dataclasses import dataclass


@dataclass
class ExportPackage:
    source_id: str
    folder: str
    files: tuple[str, ...]


def build_export_package(source_id: str, date: str) -> ExportPackage:
    return ExportPackage(
        source_id=source_id,
        folder=f"/cognix-core/{date}/{source_id}/",
        files=(
            "source.json",
            "original-reference.txt",
            "summary.md",
            "myanmar-summary.md",
            "claims.json",
            "review.json",
        ),
    )
