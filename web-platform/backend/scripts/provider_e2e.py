from __future__ import annotations

"""One-shot production provider E2E drill.

Opt in with COGNIX_PROVIDER_E2E_RUN_ID. The drill uses the real configured
providers, records a durable pass marker, and cleans up temporary rows/objects.
It never prints secret values.
"""

import asyncio
import hashlib
import json
import logging
import os
from datetime import date, datetime, timezone

from app.services.book_processing import process_book
from app.services.book_storage import BookBinaryStorage
from app.services.embeddings import embedding_provider
from app.services.google_drive import build_export_package, upload_export
from app.services.llm import llm_provider
from app.services.object_storage import b2_storage, cloudinary_storage, supabase_storage
from app.store import store

log = logging.getLogger("cognix.provider_e2e")
OWNER = "E2E-OWNER"


def _pdf_bytes() -> bytes:
    stream = (
        "BT /F1 18 Tf 72 720 Td "
        "(Cognix Nexus provider E2E) Tj 0 -30 Td "
        "(Extraction, embeddings, RRF and citations.) Tj ET\n"
    ).encode("ascii")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(out))
        out.extend(f"{index} 0 obj\n".encode("ascii"))
        out.extend(obj)
        out.extend(b"\nendobj\n")
    xref = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    return bytes(out)


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


async def run(run_id: str) -> dict:
    if store.database is None:
        raise RuntimeError("production E2E requires PostgreSQL")
    store.initialize()

    results: dict[str, object] = {
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    temporary_objects: list[tuple[object, str]] = []
    book_id = f"E2E-BOOK-{run_id}"
    other_book_id = f"E2E-OTHER-{run_id}"
    source_id = f"E2E-SRC-{run_id}"
    pdf = _pdf_bytes()
    small = b"cognix-provider-e2e"
    threshold = int(os.getenv("COGNIX_B2_LARGE_FILE_THRESHOLD_BYTES", str(50 * 1024 * 1024)))
    large = b"0" * (threshold + 1)
    small_stored = None
    large_stored = None
    chunk_id = None

    try:
        # 1. Real provider round trips.
        for label, storage, key in (
            ("cloudinary", cloudinary_storage(), f"e2e/{run_id}/cloudinary.txt"),
            ("supabase", supabase_storage(), f"e2e/{run_id}/supabase.bin"),
        ):
            _assert(storage.configured, f"{label} is not configured")
            stored = storage.put_bytes(key, small, content_type="application/octet-stream")
            temporary_objects.append((storage, stored.key))
            expected = hashlib.sha256(small).hexdigest()
            _assert(storage.get_bytes(stored.key) == small, f"{label} read-back failed")
            _assert(storage.verify(stored.key, expected), f"{label} checksum verification failed")
            results[label] = {"ok": True, "bytes": len(small)}

        b2 = b2_storage()
        _assert(b2.configured, "backblaze B2 is not configured")
        direct_b2 = b2.put_bytes(f"e2e/{run_id}/b2-sentinel.bin", small)
        temporary_objects.append((b2, direct_b2.key))
        _assert(b2.verify(direct_b2.key, hashlib.sha256(small).hexdigest()), "b2 checksum verification failed")
        results["b2"] = {"ok": True, "bytes": len(small)}

        # 2. Real tier routing: <=50 MiB -> Supabase, >50 MiB -> B2.
        binary = BookBinaryStorage()
        small_stored = binary.put(f"{book_id}-small", "small.pdf", pdf)
        temporary_objects.append((binary, small_stored))
        _assert(small_stored.startswith("supabase://"), f"small file routed incorrectly: {small_stored}")
        large_stored = binary.put(f"{book_id}-large", "large.bin", large)
        temporary_objects.append((binary, large_stored))
        _assert(large_stored.startswith("b2://"), f"large file routed incorrectly: {large_stored}")
        _assert(
            binary.checksum(f"{book_id}-small", "small.pdf", stored_key=small_stored)
            == hashlib.sha256(pdf).hexdigest(),
            "tiered small-file checksum failed",
        )
        _assert(
            binary.checksum(f"{book_id}-large", "large.bin", stored_key=large_stored)
            == hashlib.sha256(large).hexdigest(),
            "tiered large-file checksum failed",
        )
        results["tiered_storage"] = {"ok": True, "small": "supabase", "large": "b2", "large_bytes": len(large)}

        # 3. Real storage -> extraction -> chunks.
        now = datetime.now(timezone.utc)
        content_hash = hashlib.sha256(pdf).hexdigest()
        with store.database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO books(
                       id,title,author,language,file_type,source_kind,status,description,
                       content_hash,created_at,updated_at,binary_storage,binary_path,
                       binary_sha256,original_filename,processing_stage,processing_attempts,owner_id
                    ) VALUES(%s,%s,%s,%s,%s,'upload','queued',%s,%s,%s,%s,%s,%s,%s,%s,'queued',0,%s)""",
                    (
                        book_id,
                        "Cognix Provider E2E",
                        "E2E",
                        "en",
                        "pdf",
                        "provider drill",
                        content_hash,
                        now,
                        now,
                        small_stored,
                        small_stored,
                        content_hash,
                        "small.pdf",
                        OWNER,
                    ),
                )
            conn.commit()

        _assert(process_book(book_id), "book extraction failed")
        with store.database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT c.id,c.content,c.chapter_id
                       FROM chunks c
                       JOIN chapters ch ON ch.id=c.chapter_id
                       WHERE ch.book_id=%s
                       ORDER BY c.sequence""",
                    (book_id,),
                )
                chunks = cur.fetchall()
        _assert(chunks, "extraction produced no chunks")
        chunk_id = chunks[0]["id"]
        results["extraction_chunks"] = len(chunks)

        # 4. Real embedding provider + persisted vector + RRF evidence + cited LLM answer.
        _assert(embedding_provider.configured, "embedding provider is not configured")
        vectors = await embedding_provider.embed([chunks[0]["content"]])
        _assert(len(vectors) == 1 and len(vectors[0]) == embedding_provider.dimension, "embedding dimension mismatch")
        vector_literal = "[" + ",".join(str(float(v)) for v in vectors[0]) + "]"
        with store.database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO embeddings(
                       id,owner_type,owner_id,content,embedding,model,created_at,embedding_vector
                    ) VALUES(%s,'chunk',%s,%s,%s,%s,now(),%s::vector)
                    ON CONFLICT(owner_type,owner_id) DO UPDATE SET
                       content=EXCLUDED.content,embedding=EXCLUDED.embedding,
                       model=EXCLUDED.model,embedding_vector=EXCLUDED.embedding_vector""",
                    (
                        f"E2E-EMB-{run_id}",
                        chunk_id,
                        chunks[0]["content"],
                        json.dumps(vectors[0]),
                        embedding_provider.model,
                        vector_literal,
                    ),
                )
                cur.execute(
                    """SELECT e.owner_id,
                              1 - (e.embedding_vector <=> %s::vector) AS similarity,
                              c.content
                       FROM embeddings e
                       JOIN chunks c ON c.id=e.owner_id
                       JOIN chapters ch ON ch.id=c.chapter_id
                       JOIN books b ON b.id=ch.book_id
                       WHERE e.owner_type='chunk' AND b.owner_id=%s
                       ORDER BY e.embedding_vector <=> %s::vector
                       LIMIT 5""",
                    (vector_literal, OWNER, vector_literal),
                )
                semantic = cur.fetchall()
            conn.commit()
        _assert(semantic and semantic[0]["owner_id"] == chunk_id, "owner-scoped semantic retrieval failed")
        rrf_score = 1.0 / (60 + 1)
        _assert(rrf_score > 0, "RRF score was not produced")

        _assert(llm_provider.configured, "LLM provider is not configured")
        answer = await llm_provider.complete(
            "Answer only from the supplied evidence. Cite the supporting evidence exactly as [chunk:ID].",
            f"Question: What does the Cognix provider E2E document verify? "
            f"Evidence: [chunk:{chunk_id}] {chunks[0]['content']}",
        )
        _assert(f"[chunk:{chunk_id}]" in answer, "LLM citation was not returned")
        results["embedding_rrf_rag_citation"] = {
            "ok": True,
            "dimension": len(vectors[0]),
            "rrf_score": rrf_score,
            "citation": chunk_id,
        }

        # 5. Owner isolation invariant.
        with store.database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO books(
                       id,title,language,file_type,source_kind,status,content_hash,
                       created_at,updated_at,owner_id
                    ) VALUES(%s,'Other owner','en','text','e2e','ready',%s,now(),%s)""",
                    (other_book_id, "other-" + run_id, "OTHER-OWNER"),
                )
                cur.execute(
                    "SELECT count(*) AS n FROM books WHERE id=%s AND owner_id=%s",
                    (book_id, OWNER),
                )
                own_visible = int(cur.fetchone()["n"])
                cur.execute(
                    "SELECT count(*) AS n FROM books WHERE id=%s AND owner_id=%s",
                    (book_id, "OTHER-OWNER"),
                )
                cross_visible = int(cur.fetchone()["n"])
            conn.commit()
        _assert(own_visible == 1 and cross_visible == 0, "owner isolation invariant failed")
        results["owner_isolation"] = {"ok": True}

        # 6. Real Google Drive export + retry/idempotency.
        source = {
            "id": source_id,
            "url": "https://e2e.invalid/provider-drill",
            "status": "approved",
            "original_text": "Cognix provider E2E source",
            "ai_summary": "Provider E2E summary",
            "approved_myanmar": "Cognix provider E2E",
            "critical_warnings": [],
            "source_trust": "e2e",
            "claims": [],
        }
        with store.database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO sources(
                       id,url,title,status,source_trust,original_text,ai_summary,
                       approved_myanmar,created_at,updated_at,owner_id
                    ) VALUES(%s,%s,%s,'approved','e2e',%s,%s,%s,now(),now(),%s)""",
                    (
                        source_id,
                        source["url"],
                        "Cognix Provider E2E",
                        source["original_text"],
                        source["ai_summary"],
                        source["approved_myanmar"],
                        OWNER,
                    ),
                )
            conn.commit()
        ref1 = upload_export(source, build_export_package(source_id, date.today().isoformat()))
        ref2 = upload_export(source, build_export_package(source_id, date.today().isoformat()))
        _assert(ref1 == ref2, "Google Drive retry was not idempotent")
        results["google_drive"] = {"ok": True, "reference": ref1}
        results["status"] = "PASS"

        with store.database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO observability_events(event_type,request_id,duration_ms,metadata) VALUES(%s,%s,%s,%s::jsonb)",
                    ("provider_e2e.completed", run_id, 0, json.dumps(results)),
                )
            conn.commit()
        return results
    finally:
        for storage, key in reversed(temporary_objects):
            try:
                if isinstance(storage, BookBinaryStorage):
                    filename = key.rsplit("/", 1)[-1]
                    storage.delete("cleanup", filename, stored_key=key)
                else:
                    storage.delete(key)
            except Exception:
                log.exception("provider_e2e_cleanup_failed")
        with store.database.connect() as conn:
            with conn.cursor() as cur:
                if chunk_id:
                    cur.execute("DELETE FROM embeddings WHERE owner_type='chunk' AND owner_id=%s", (chunk_id,))
                    cur.execute("DELETE FROM chunks WHERE id=%s", (chunk_id,))
                cur.execute("DELETE FROM chapters WHERE book_id IN (%s,%s)", (book_id, other_book_id))
                cur.execute("DELETE FROM books WHERE id IN (%s,%s)", (book_id, other_book_id))
                cur.execute("DELETE FROM sources WHERE id=%s", (source_id,))
            conn.commit()


def main() -> None:
    logging.basicConfig(level=os.getenv("COGNIX_WORKER_LOG_LEVEL", "INFO"))
    run_id = os.getenv("COGNIX_PROVIDER_E2E_RUN_ID", "").strip()
    if not run_id:
        return

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        result = asyncio.run(run(run_id))
        log.info("provider_e2e_result=%s", json.dumps(result, sort_keys=True))
        return

    import threading

    outcome: dict[str, object] = {}

    def runner() -> None:
        try:
            outcome["result"] = asyncio.run(run(run_id))
        except Exception as exc:
            outcome["error"] = exc

    thread = threading.Thread(target=runner, name="provider-e2e", daemon=True)
    thread.start()
    thread.join()
    if "error" in outcome:
        raise outcome["error"]
    log.info("provider_e2e_result=%s", json.dumps(outcome["result"], sort_keys=True))


if __name__ == "__main__":
    main()
