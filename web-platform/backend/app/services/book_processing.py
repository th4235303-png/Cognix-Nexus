from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from app.services.book_ingestion import extract_document
from app.services.book_storage import BookBinaryStorage
from app.store import store


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


def _claim_book(book_id: str) -> dict | None:
    db = store.database
    if db is None or not db.try_claim_task(f"book:{book_id}"):
        return None
    try:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM books WHERE id=%s FOR UPDATE", (book_id,))
                book = cur.fetchone()
                if not book:
                    db.release_task(f"book:{book_id}")
                    return None
                attempts = int(book.get("processing_attempts") or 0)
                if book["status"] == "ready" or attempts >= 3:
                    db.release_task(f"book:{book_id}")
                    return None
                now = datetime.now(timezone.utc)
                cur.execute(
                    """UPDATE books
                       SET status='processing',
                           processing_stage='extracting',
                           processing_attempts=%s,
                           processing_error=NULL,
                           processing_started_at=%s,
                           updated_at=now()
                       WHERE id=%s""",
                    (attempts + 1, now, book_id),
                )
            conn.commit()
        return {**book, "processing_attempts": attempts + 1}
    except Exception:
        db.release_task(f"book:{book_id}")
        raise


def _mark_failed(book_id: str, error: str) -> None:
    db = store.database
    if db is None:
        return
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE books
                   SET status='failed',
                       processing_stage='failed',
                       processing_error=%s,
                       updated_at=now()
                   WHERE id=%s""",
                (error[:4000], book_id),
            )
        conn.commit()


def process_book(book_id: str) -> bool:
    db = store.database
    if db is None:
        return False
    book = _claim_book(book_id)
    if not book:
        return False
    try:
        filename = book.get("original_filename") or Path(book["binary_path"]).name
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

        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM embeddings WHERE owner_type='chunk' AND owner_id IN "
                    "(SELECT c.id FROM chunks c JOIN chapters ch ON ch.id=c.chapter_id WHERE ch.book_id=%s)",
                    (book_id,),
                )
                cur.execute("DELETE FROM chunks WHERE chapter_id IN (SELECT id FROM chapters WHERE book_id=%s)", (book_id,))
                cur.execute("DELETE FROM chapters WHERE book_id=%s", (book_id,))
                cur.executemany(
                    "INSERT INTO chapters(id,book_id,chapter_number,title,created_at) VALUES(%s,%s,%s,%s,%s)",
                    chapters,
                )
                cur.executemany(
                    """INSERT INTO chunks(
                        id,chapter_id,sequence,content,page_number,start_offset,end_offset,token_count,created_at
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    chunks,
                )
                cur.execute(
                    """UPDATE books
                       SET title=%s, author=%s, status='processing',
                           processing_stage='embedding',
                           processing_error=NULL,
                           updated_at=now()
                       WHERE id=%s""",
                    (document.title, document.author, book_id),
                )
            conn.commit()
        return True
    except Exception as exc:
        _mark_failed(book_id, str(exc))
        return False
    finally:
        db.release_task(f"book:{book_id}")


def process_queued_books(limit: int = 2) -> int:
    db = store.database
    if db is None:
        return 0
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id FROM books
                   WHERE source_kind='upload'
                     AND binary_path IS NOT NULL
                     AND binary_storage IS NOT NULL
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
            if ids:
                cur.execute(
                    """UPDATE books
                       SET status='ready', processing_stage='completed',
                           processing_error=NULL, processed_at=now(), updated_at=now()
                       WHERE id = ANY(%s)""",
                    (ids,),
                )
        conn.commit()
    return len(ids)
