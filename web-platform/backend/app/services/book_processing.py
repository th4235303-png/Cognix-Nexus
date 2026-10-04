from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from app.services.book_ingestion import extract_document
from app.services.book_storage import BookBinaryStorage
from app.services.lease_runner import LeaseLostError, run_with_lease_heartbeat
from app.store import store

logger = logging.getLogger("cognix.worker")


def _chunk_text(text: str, size: int = 1800) -> list[str]:
    paragraphs = [part.strip() for part in text.replace("\r\n", "\n").split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip()
        if len(candidate) <= size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(paragraph) <= size:
                current = paragraph
            else:
                chunks.extend(paragraph[i:i + size] for i in range(0, len(paragraph), size))
                current = ""
    if current:
        chunks.append(current)
    return chunks


def _claim_book(book_id: str) -> tuple[dict, str] | None:
    db = store.database
    if db is None:
        return None
    return db.claim_book_processing(book_id)


def _mark_failed(book_id: str, token: str, error: str) -> bool:
    db = store.database
    if db is None:
        return False
    return db.fail_book_processing(book_id, token, error)


def process_book(book_id: str) -> bool:
    db = store.database
    if db is None:
        return False
    claimed = _claim_book(book_id)
    if claimed is None:
        logger.info("book_processing_claim_skipped book_id=%s", book_id)
        return False
    book, token = claimed
    logger.info(
        "book_processing_claimed book_id=%s attempt=%s",
        book_id,
        book["processing_attempts"],
    )

    def process_claimed(lease_is_valid) -> bool:
        try:
            binary_path = book.get("binary_path")
            binary_storage = book.get("binary_storage")
            filename = (
                book.get("original_filename")
                or (Path(binary_path).name if binary_path else None)
                or (Path(binary_storage).name if binary_storage else None)
                or f"document.{str(book.get('file_type') or 'pdf').lstrip('.')}"
            )
            if not filename or filename == ".":
                raise RuntimeError("Book binary metadata is incomplete: filename/path is missing")
            data = BookBinaryStorage().get(book_id, filename)
            import hashlib
            checksum = hashlib.sha256(data).hexdigest()
            if checksum.lower() != str(book.get("binary_sha256") or book.get("content_hash")).lower():
                raise RuntimeError("Book binary checksum mismatch")

            document = extract_document(data, filename, book["file_type"])
            if not document.sections:
                raise RuntimeError("No extractable pages or sections were found")

            now = datetime.now(timezone.utc)
            chapters: list[tuple] = []
            chunks: list[tuple] = []
            for chapter_number, section in enumerate(document.sections, start=1):
                chapter_id = f"CH-{book_id}-{chapter_number:04d}"
                title = section.get("title") or f"Section {chapter_number}"
                chapters.append((chapter_id, book_id, chapter_number, title, now))
                for sequence, content in enumerate(_chunk_text(section.get("text", "")), start=1):
                    if not content.strip():
                        continue
                    chunk_id = f"CHK-{book_id}-{chapter_number:04d}-{sequence:04d}"
                    chunks.append(
                        (
                            chunk_id, chapter_id, sequence, content.strip(),
                            section.get("page_number"), None, None,
                            max(1, len(content.split())), now,
                        )
                    )
            if not chunks:
                raise RuntimeError("Extraction produced no chunks")
            if not lease_is_valid():
                raise LeaseLostError(f"Book processing lease lost for {book_id}")
            if not db.complete_book_extraction(
                book_id, token, document.title, document.author, chapters, chunks
            ):
                raise LeaseLostError(f"Book processing lease lost before persistence for {book_id}")
            logger.info("book_processing_extraction_completed book_id=%s", book_id)
            return True
        except LeaseLostError:
            raise
        except Exception as exc:
            if not lease_is_valid():
                raise LeaseLostError(f"Book processing lease lost for {book_id}") from exc
            if not _mark_failed(book_id, token, str(exc)):
                raise LeaseLostError(f"Book processing lease lost before failure persistence for {book_id}") from exc
            logger.warning(
                "book_processing_failed book_id=%s error_type=%s",
                book_id,
                type(exc).__name__,
            )
            return False

    try:
        return run_with_lease_heartbeat(
            "book_processing",
            book_id,
            lambda: db.renew_book_processing_claim(book_id, token),
            process_claimed,
        )
    except LeaseLostError:
        logger.warning("book_processing_lease_lost book_id=%s", book_id)
        return False


def process_queued_books(limit: int = 2) -> int:
    db = store.database
    if db is None:
        return 0
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id FROM books
                   WHERE source_kind='upload'
                     AND (binary_path IS NOT NULL OR binary_storage IS NOT NULL OR original_filename IS NOT NULL)
                     AND status IN ('queued','processing','failed')
                     AND processing_attempts < 3
                     AND (
                       status <> 'processing'
                       OR processing_started_at IS NULL
                       OR processing_started_at < now() - interval '15 minutes'
                     )
                   ORDER BY created_at
                   LIMIT %s""",
                (limit,),
            )
            ids = [row["id"] for row in cur.fetchall()]
    return sum(1 for book_id in ids if process_book(book_id))


def finalize_indexed_books() -> int:
    db = store.database
    if db is None:
        return 0
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT b.id
                   FROM books b
                   WHERE b.status='processing' AND b.processing_stage='embedding'
                     AND EXISTS (
                       SELECT 1 FROM chunks c
                       JOIN chapters ch ON ch.id=c.chapter_id
                       WHERE ch.book_id=b.id
                     )
                     AND NOT EXISTS (
                       SELECT 1 FROM chunks c
                       JOIN chapters ch ON ch.id=c.chapter_id
                       LEFT JOIN embeddings e ON e.owner_type='chunk' AND e.owner_id=c.id
                       WHERE ch.book_id=b.id AND e.owner_id IS NULL
                     )"""
            )
            ids = [row["id"] for row in cur.fetchall()]
    completed = 0
    for book_id in ids:
        token = db.claim_book_finalization(book_id)
        if token is None:
            continue
        try:
            if db.complete_book_finalization(book_id, token):
                completed += 1
                logger.info("book_processing_completed book_id=%s", book_id)
            else:
                db.release_book_claim(book_id, token)
                logger.info("book_processing_finalization_deferred book_id=%s", book_id)
        except Exception:
            db.release_book_claim(book_id, token)
            raise
    return completed
