from __future__ import annotations

from hashlib import sha256
import os
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.book_storage import BookBinaryStorage
from app.services.upload_limits import UploadTooLargeError, read_upload_limited
from app.store import now_iso, store

router = APIRouter(prefix="/brain", tags=["brain-vault"])


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    author: str | None = Field(default=None, max_length=500)
    language: str = Field(default="en", min_length=2, max_length=16)
    file_type: str = Field(default="text", min_length=1, max_length=16)
    source_url: str | None = None
    description: str | None = None
    text: str = Field(min_length=1)


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    note_type: str = Field(default="note", max_length=50)
    status: str = Field(default="draft", max_length=50)
    source_type: str | None = None
    source_id: str | None = None


class ConceptCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    description: str | None = None


class ConceptLinkCreate(BaseModel):
    from_concept_id: str
    to_concept_id: str
    relation: str = Field(default="related", max_length=80)
    weight: float = Field(default=1, ge=0, le=1)


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
            current = paragraph
    if current:
        chunks.append(current)
    if not chunks and text.strip():
        chunks = [text.strip()[i:i + size] for i in range(0, len(text.strip()), size)]
    return chunks


def _book_from_store(book_id: str) -> dict:
    book = store.brain_books.get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book


@router.get("/books")
def list_books(limit: int = 50, offset: int = 0) -> dict:
    if store.database is None:
        items = sorted(store.brain_books.values(), key=lambda item: item["updated_at"], reverse=True)
        return {"items": items[offset:offset + min(limit, 100)], "total": len(items)}
    items, total = store.database.list_books(limit=limit, offset=offset)
    return {"items": items, "total": total, "limit": min(max(limit, 1), 100), "offset": max(offset, 0)}


@router.post("/books", status_code=201)
def create_book(payload: BookCreate) -> dict:
    now = now_iso()
    book_id = f"BOOK-{uuid4().hex[:8].upper()}"
    paragraphs = _chunk_text(payload.text)
    chapter_id = f"CH-{uuid4().hex[:8].upper()}"
    chunks = []
    for index, content in enumerate(paragraphs, start=1):
        chunks.append({
            "id": f"CHK-{uuid4().hex[:8].upper()}",
            "chapter_id": chapter_id,
            "sequence": index,
            "content": content,
            "page_number": None,
            "start_offset": None,
            "end_offset": None,
            "token_count": max(1, len(content.split())),
            "created_at": now,
        })
    chapters = [{
        "id": chapter_id,
        "book_id": book_id,
        "chapter_number": 1,
        "title": "Imported Content",
        "created_at": now,
        "chunks": chunks,
    }]
    book = {
        "id": book_id,
        "title": payload.title,
        "author": payload.author,
        "language": payload.language,
        "file_type": payload.file_type.lower(),
        "source_kind": "imported_text",
        "source_url": payload.source_url,
        "status": "ready",
        "description": payload.description,
        "content_hash": sha256(payload.text.encode("utf-8")).hexdigest(),
        "created_at": now,
        "updated_at": now,
        "chapters": chapters,
        "chunk_count": len(chunks),
    }
    store.brain_books[book_id] = book
    store.save_brain_book(book)
    store.add_activity("brain_book_created", book_id, "new", "ready")
    return book


@router.get("/books/{book_id}")
def get_book(book_id: str) -> dict:
    if store.database is not None:
        book = store.database.get_book(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book
    return _book_from_store(book_id)


@router.get("/books/{book_id}/chapters")
def list_chapters(book_id: str) -> dict:
    book = get_book(book_id)
    chapters = [{k: v for k, v in chapter.items() if k != "chunks"} for chapter in book["chapters"]]
    return {"items": chapters, "total": len(chapters)}


@router.get("/books/{book_id}/chapters/{chapter_id}")
def get_chapter(book_id: str, chapter_id: str) -> dict:
    book = get_book(book_id)
    chapter = next((item for item in book["chapters"] if item["id"] == chapter_id), None)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.get("/books/{book_id}/search")
def search_book(book_id: str, q: str) -> dict:
    if store.database is not None:
        if not store.database.get_book(book_id):
            raise HTTPException(status_code=404, detail="Book not found")
        matches, total = store.database.search_book(book_id, q)
        return {"query": q, "items": matches, "total": total}
    book = _book_from_store(book_id)
    query = q.strip().lower()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    terms = [term for term in query.split() if term]
    matches = []
    for chapter in book["chapters"]:
        for chunk in chapter["chunks"]:
            haystack = chunk["content"].lower()
            score = sum(haystack.count(term) for term in terms)
            if score:
                matches.append({"chunk_id": chunk["id"], "chapter_id": chapter["id"], "chapter_title": chapter["title"], "sequence": chunk["sequence"], "score": score, "content": chunk["content"]})
    matches.sort(key=lambda item: item["score"], reverse=True)
    return {"query": q, "items": matches[:20], "total": len(matches)}


@router.get("/notes")
def list_notes() -> dict:
    store.refresh()
    items = sorted(store.brain_notes.values(), key=lambda item: item["updated_at"], reverse=True)
    return {"items": items, "total": len(items)}


@router.post("/notes", status_code=201)
def create_note(payload: NoteCreate) -> dict:
    now = now_iso()
    note_id = f"NOTE-{uuid4().hex[:8].upper()}"
    note = {
        "id": note_id,
        "title": payload.title,
        "content": payload.content,
        "note_type": payload.note_type,
        "status": payload.status,
        "created_at": now,
        "updated_at": now,
        "source_type": payload.source_type,
        "source_id": payload.source_id,
    }
    store.brain_notes[note_id] = note
    store.save_brain_note(note)
    store.add_activity("brain_note_created", note_id, "new", payload.status)
    return note


@router.get("/notes/{note_id}/backlinks")
def note_backlinks(note_id: str) -> dict:
    store.refresh()
    if note_id not in store.brain_notes:
        raise HTTPException(status_code=404, detail="Note not found")
    items = []
    for note in store.brain_notes.values():
        for source in note.get("sources", []):
            if source["source_type"] == "note" and source["source_id"] == note_id:
                items.append(note)
                break
    return {"items": items, "total": len(items)}


@router.get("/concepts")
def list_concepts() -> dict:
    store.refresh()
    items = sorted(store.brain_concepts.values(), key=lambda item: item["name"].lower())
    return {"items": items, "total": len(items)}


@router.post("/concepts", status_code=201)
def create_concept(payload: ConceptCreate) -> dict:
    now = now_iso()
    existing = next((item for item in store.brain_concepts.values() if item["name"].casefold() == payload.name.casefold()), None)
    if existing:
        return existing
    concept_id = f"CON-{uuid4().hex[:8].upper()}"
    concept = {
        "id": concept_id,
        "name": payload.name,
        "description": payload.description,
        "created_at": now,
        "updated_at": now,
    }
    store.brain_concepts[concept_id] = concept
    store.save_brain_concept(concept)
    store.add_activity("brain_concept_created", concept_id, "new", "active")
    return concept


@router.get("/graph")
def get_graph() -> dict:
    store.refresh()
    return {
        "nodes": list(store.brain_concepts.values()),
        "edges": list(store.brain_concept_links.values()),
    }


@router.get("/query")
def query_brain(q: str, limit: int = 12) -> dict:
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    limit = max(1, min(limit, 50))
    if store.database is not None:
        terms = [term for term in query.lower().split() if term]
        pattern = "%" + "%".join(terms) + "%"
        with store.database.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT b.id AS book_id, b.title AS book_title,
                              ch.id AS chapter_id, c.id AS chunk_id,
                              ch.title AS chapter_title, c.sequence, c.content
                       FROM chunks c
                       JOIN chapters ch ON ch.id=c.chapter_id
                       JOIN books b ON b.id=ch.book_id
                       WHERE lower(c.content) LIKE %s
                       ORDER BY c.created_at DESC
                       LIMIT %s""",
                    (pattern, limit),
                )
                rows = cur.fetchall()
        items = []
        for row in rows:
            haystack = row["content"].lower()
            score = sum(haystack.count(term) for term in terms)
            items.append({
                "book_id": row["book_id"], "book_title": row["book_title"],
                "chapter_id": row["chapter_id"], "chapter_title": row["chapter_title"],
                "chunk_id": row["chunk_id"], "sequence": row["sequence"],
                "score": score, "content": row["content"],
            })
        items.sort(key=lambda item: item["score"], reverse=True)
        return {
            "query": q, "mode": "evidence_search", "answer": None,
            "items": items, "total": len(items),
            "message": "Semantic embeddings and LLM synthesis are not enabled yet; results are evidence-ranked text matches.",
        }
    query = query.lower()
    terms = [term for term in query.split() if term]
    evidence = []
    for book in store.brain_books.values():
        for chapter in book["chapters"]:
            for chunk in chapter["chunks"]:
                score = sum(chunk["content"].lower().count(term) for term in terms)
                if score:
                    evidence.append({"book_id": book["id"], "book_title": book["title"], "chapter_id": chapter["id"], "chunk_id": chunk["id"], "score": score, "content": chunk["content"]})
    evidence.sort(key=lambda item: item["score"], reverse=True)
    return {"query": q, "mode": "evidence_search", "answer": None, "items": evidence[:limit], "total": len(evidence),
            "message": "Semantic embeddings and LLM synthesis are not enabled yet; results are evidence-ranked text matches."}


@router.post("/concept-links", status_code=201)
def create_concept_link(payload: ConceptLinkCreate) -> dict:
    store.refresh()
    if payload.from_concept_id not in store.brain_concepts or payload.to_concept_id not in store.brain_concepts:
        raise HTTPException(status_code=404, detail="Concept not found")
    existing = next(
        (
            link for link in store.brain_concept_links.values()
            if link["from_concept_id"] == payload.from_concept_id
            and link["to_concept_id"] == payload.to_concept_id
            and link["relation"] == payload.relation
        ),
        None,
    )
    if existing:
        return existing
    link = {
        "id": f"CL-{uuid4().hex[:8].upper()}",
        "from_concept_id": payload.from_concept_id,
        "to_concept_id": payload.to_concept_id,
        "relation": payload.relation,
        "weight": payload.weight,
        "created_at": now_iso(),
    }
    store.brain_concept_links[link["id"]] = link
    store.save_brain_concept_link(link)
    store.add_activity("brain_concept_linked", link["id"], "new", "active")
    return link


@router.post("/books/upload", status_code=201)
async def upload_book(file: UploadFile = File(...), language: str = "en", description: str | None = None) -> dict:
    """Persist a PDF/EPUB and enqueue worker-owned extraction.

    The API never performs document extraction. This keeps large uploads off the
    request path and makes API/worker storage shared and retryable.
    """
    filename = file.filename or "document"
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in {"pdf", "epub"}:
        raise HTTPException(status_code=400, detail="Only PDF and EPUB uploads are supported")
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required for book uploads")

    max_upload_bytes = 50 * 1024 * 1024
    try:
        data = await read_upload_limited(file, max_upload_bytes)
    except UploadTooLargeError as exc:
        raise HTTPException(status_code=413, detail="Document exceeds the 50 MB upload limit") from exc
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded document is empty")

    content_hash = sha256(data).hexdigest()
    with store.database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM books WHERE content_hash=%s ORDER BY created_at LIMIT 1", (content_hash,))
            existing = cur.fetchone()
    if existing:
        return {"id": existing["id"], "status": existing["status"], "processing_stage": existing.get("processing_stage") or "queued",
                "content_hash": content_hash, "idempotent": True, "book": store._book_row(existing)}

    book_id = f"BOOK-{uuid4().hex[:8].upper()}"
    binary_path = None
    try:
        binary_path = BookBinaryStorage().put(book_id, filename, data)
        now = now_iso()
        book = {
            "id": book_id,
            "title": filename.rsplit(".", 1)[0] or "Untitled",
            "author": None,
            "language": language,
            "file_type": suffix,
            "source_kind": "upload",
            "source_url": None,
            "status": "queued",
            "description": description,
            "content_hash": content_hash,
            "created_at": now,
            "updated_at": now,
            "chapters": [],
            "chunk_count": 0,
            "original_filename": filename,
            "binary_storage": os.getenv("COGNIX_BOOK_STORAGE_PROVIDER", "local").strip().lower(),
            "binary_path": binary_path,
            "binary_sha256": content_hash,
            "processing_stage": "queued",
            "processing_attempts": 0,
            "processing_error": None,
            "processing_started_at": None,
            "processed_at": None,
        }
        store.save_brain_book(book)
        store.refresh()
        saved = store.brain_books.get(book_id) or book
        store.add_activity("brain_book_uploaded", book_id, "new", "queued")
        return {"id": book_id, "status": "queued", "processing_stage": "queued", "content_hash": content_hash,
                "idempotent": False, "book": saved}
    except Exception as exc:
        if binary_path:
            try:
                BookBinaryStorage().delete(book_id, filename)
            except Exception:
                pass
        if "duplicate key" in str(exc).lower() and store.database:
            with store.database.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM books WHERE content_hash=%s ORDER BY created_at LIMIT 1", (content_hash,))
                    existing = cur.fetchone()
            if existing:
                return {"id": existing["id"], "status": existing["status"], "processing_stage": existing.get("processing_stage") or "queued",
                        "content_hash": content_hash, "idempotent": True, "book": store._book_row(existing)}
        raise HTTPException(status_code=503, detail=f"Book upload could not be persisted: {exc}") from exc
