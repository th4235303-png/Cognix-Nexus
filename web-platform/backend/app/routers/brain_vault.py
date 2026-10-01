from __future__ import annotations

from hashlib import sha256
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.services.book_ingestion import extract_document
from app.services.book_storage import BookBinaryStorage
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
def list_books() -> dict:
    store.refresh()
    items = sorted(store.brain_books.values(), key=lambda item: item["updated_at"], reverse=True)
    return {"items": items, "total": len(items)}


@router.post("/books", status_code=201)
def create_book(payload: BookCreate) -> dict:
    try:
        binary_path = BookBinaryStorage().put(book_id, filename, data)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    now = now_iso()
    chapters = []
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
    chapters.append({
        "id": chapter_id,
        "book_id": book_id,
        "chapter_number": 1,
        "title": "Imported Content",
        "created_at": now,
        "chunks": chunks,
    })
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
    store.refresh()
    return _book_from_store(book_id)


@router.get("/books/{book_id}/chapters")
def list_chapters(book_id: str) -> dict:
    book = _book_from_store(book_id)
    chapters = [{k: v for k, v in chapter.items() if k != "chunks"} for chapter in book["chapters"]]
    return {"items": chapters, "total": len(chapters)}


@router.get("/books/{book_id}/chapters/{chapter_id}")
def get_chapter(book_id: str, chapter_id: str) -> dict:
    book = _book_from_store(book_id)
    chapter = next((item for item in book["chapters"] if item["id"] == chapter_id), None)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.get("/books/{book_id}/search")
def search_book(book_id: str, q: str) -> dict:
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
                matches.append({
                    "chunk_id": chunk["id"],
                    "chapter_id": chapter["id"],
                    "chapter_title": chapter["title"],
                    "sequence": chunk["sequence"],
                    "score": score,
                    "content": chunk["content"],
                })
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
def query_brain(q: str) -> dict:
    query = q.strip().lower()
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    terms = [term for term in query.split() if term]
    evidence = []
    for book in store.brain_books.values():
        for chapter in book["chapters"]:
            for chunk in chapter["chunks"]:
                score = sum(chunk["content"].lower().count(term) for term in terms)
                if score:
                    evidence.append({
                        "book_id": book["id"],
                        "book_title": book["title"],
                        "chapter_id": chapter["id"],
                        "chunk_id": chunk["id"],
                        "score": score,
                        "content": chunk["content"],
                    })
    evidence.sort(key=lambda item: item["score"], reverse=True)
    return {
        "query": q,
        "mode": "evidence_search",
        "answer": None,
        "items": evidence[:12],
        "total": len(evidence),
        "message": "Semantic embeddings and LLM synthesis are not enabled yet; results are evidence-ranked text matches.",
    }


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
    filename = file.filename or "document"
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in {"pdf", "epub"}:
        raise HTTPException(status_code=400, detail="Only PDF and EPUB uploads are supported")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded document is empty")
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Document exceeds the 25 MB upload limit")
    try:
        document = extract_document(data, filename, suffix)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Document extraction failed: {exc}") from exc

    now = now_iso()
    book_id = f"BOOK-{uuid4().hex[:8].upper()}"
    chapters = []
    total_chunks = 0
    for chapter_number, section in enumerate(document.sections, start=1):
        section_text = section["text"]
        chunks = []
        for index, content in enumerate(_chunk_text(section_text), start=1):
            chunk = {
                "id": f"CHK-{uuid4().hex[:8].upper()}",
                "chapter_id": "",
                "sequence": index,
                "content": content,
                "page_number": section.get("page_number"),
                "source_section": section.get("title"),
                "start_offset": None,
                "end_offset": None,
                "token_count": max(1, len(content.split())),
                "created_at": now,
            }
            chunks.append(chunk)
        chapter_id = f"CH-{uuid4().hex[:8].upper()}"
        for chunk in chunks:
            chunk["chapter_id"] = chapter_id
        chapters.append({
            "id": chapter_id,
            "book_id": book_id,
            "chapter_number": chapter_number,
            "title": section.get("title") or f"Section {chapter_number}",
            "created_at": now,
            "chunks": chunks,
        })
        total_chunks += len(chunks)

    book = {
        "id": book_id,
        "title": document.title,
        "author": document.author,
        "language": language,
        "file_type": document.file_type,
        "source_kind": "upload",
        "source_url": None,
        "status": "ready",
        "description": description,
        "content_hash": sha256(data).hexdigest(),
        "created_at": now,
        "updated_at": now,
        "chapters": chapters,
        "chunk_count": total_chunks,
        "original_filename": filename,
        "binary_storage": "filesystem",
        "binary_path": binary_path,
    }
    store.brain_books[book_id] = book
    store.save_brain_book(book)
    store.add_activity("brain_book_uploaded", book_id, "new", "ready")
    return book
