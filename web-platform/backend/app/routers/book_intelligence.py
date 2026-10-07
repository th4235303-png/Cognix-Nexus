from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.ownership import get_book_for_request, owner_for_request
from app.services.llm import llm_provider
from app.store import store

router = APIRouter(prefix="/brain", tags=["book-intelligence"])


def db():
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required")
    return store.database


def owner(request: Request) -> str:
    value = owner_for_request(request)
    if not value:
        raise HTTPException(status_code=401, detail="Authenticated owner is required")
    return value


@router.get("/books/{book_id}/progress")
def progress(book_id: str, request: Request):
    own = owner(request)
    get_book_for_request(request, book_id)
    database = db()
    with database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM book_reading_progress WHERE book_id=%s AND owner_id=%s", (book_id, own))
            row = cur.fetchone()
    return row or {"book_id": book_id, "status": "queued", "percent": 0, "completed_units": 0, "total_units": 0}


@router.get("/books/{book_id}/timeline")
def timeline(book_id: str, request: Request):
    own = owner(request)
    get_book_for_request(request, book_id)
    database = db()
    with database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id,event_type,stage,percent,chapter_id,chapter_number,message,metadata,created_at "
                "FROM reading_events WHERE book_id=%s AND owner_id=%s ORDER BY created_at DESC LIMIT 200",
                (book_id, own),
            )
            rows = cur.fetchall()
    return {"items": rows, "total": len(rows)}


@router.get("/books/{book_id}/ledger.md")
def ledger(book_id: str, request: Request):
    own = owner(request)
    book = get_book_for_request(request, book_id)
    database = db()
    with database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT created_at,event_type,stage,percent,message FROM reading_events "
                "WHERE book_id=%s AND owner_id=%s ORDER BY created_at",
                (book_id, own),
            )
            rows = cur.fetchall()
    lines = ["# " + book["title"], "", "Category: " + str(book.get("category") or "Unclassified"), ""]
    lines += [
        "- %s | %s | %s | %s%% | %s" % (
            row["created_at"].isoformat(), row["event_type"], row["stage"], row["percent"] or 0, row["message"] or ""
        )
        for row in rows
    ]
    return "\n".join(lines)


@router.get("/knowledge")
def knowledge(request: Request, category: str | None = None, book_id: str | None = None, limit: int = 100):
    own = owner(request)
    database = db()
    limit = max(1, min(limit, 500))
    clauses = ["owner_id=%s"]
    params = [own]
    if category:
        clauses.append("category=%s")
        params.append(category)
    if book_id:
        clauses.append("book_id=%s")
        params.append(book_id)
    with database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM knowledge_items WHERE " + " AND ".join(clauses) + " ORDER BY created_at DESC LIMIT %s",
                (*params, limit),
            )
            rows = cur.fetchall()
    return {"items": rows, "total": len(rows)}


class SynthesisRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    category: str | None = None
    topic: str | None = None
    book_ids: list[str] = Field(default_factory=list)


async def _synthesize(payload: SynthesisRequest, request: Request, derived: bool = False):
    own = owner(request)
    database = db()
    if not llm_provider.configured:
        raise HTTPException(status_code=503, detail="LLM synthesis is not configured")
    clauses = ["owner_id=%s"]
    params = [own]
    if payload.category:
        clauses.append("category=%s")
        params.append(payload.category)
    if payload.book_ids:
        clauses.append("book_id = ANY(%s)")
        params.append(payload.book_ids)
    with database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id,book_id,category,knowledge_type,title,content FROM knowledge_items WHERE "
                + " AND ".join(clauses)
                + " ORDER BY created_at DESC LIMIT 200",
                (*params,),
            )
            rows = cur.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="No knowledge items matched")
    evidence = "\n\n".join(
        "[knowledge:%s] %s: %s" % (row["id"], row["title"] or row["knowledge_type"], row["content"])
        for row in rows
    )
    system = (
        "You create a transformative study artifact from source-linked knowledge. "
        "Do not invent facts or reproduce source books verbatim. Preserve disagreement and cite [knowledge:ID]."
    )
    content = await llm_provider.complete(
        system,
        "Title: %s\nCategory: %s\nTopic: %s\n\n%s"
        % (payload.title, payload.category or "Mixed", payload.topic or "General", evidence),
    )
    source_books = sorted({row["book_id"] for row in rows})
    source_knowledge = [row["id"] for row in rows]
    table = "derived_books" if derived else "lesson_packs"
    prefix = "DBOOK" if derived else "LESSON"
    identifier = f"{prefix}-{uuid4().hex[:8].upper()}"
    with database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO " + table
                + "(id,owner_id,title,category,topic,status,content,source_book_ids,source_knowledge_ids,model) "
                + "VALUES(%s,%s,%s,%s,%s,'draft',%s,%s::jsonb,%s::jsonb,%s)",
                (identifier, own, payload.title, payload.category, payload.topic, content, json.dumps(source_books), json.dumps(source_knowledge), llm_provider.model),
            )
        conn.commit()
    return {
        "id": identifier,
        "title": payload.title,
        "content": content,
        "source_book_ids": source_books,
        "source_knowledge_ids": source_knowledge,
    }


@router.post("/lessons/generate", status_code=201)
async def generate_lesson(payload: SynthesisRequest, request: Request):
    return await _synthesize(payload, request, False)


@router.get("/lessons")
def list_lessons(request: Request, limit: int = 50):
    own = owner(request)
    database = db()
    limit = max(1, min(limit, 200))
    with database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM lesson_packs WHERE owner_id=%s ORDER BY updated_at DESC LIMIT %s", (own, limit))
            rows = cur.fetchall()
    return {"items": rows, "total": len(rows)}


@router.post("/derived-books/generate", status_code=201)
async def generate_derived_book(payload: SynthesisRequest, request: Request):
    return await _synthesize(payload, request, True)


@router.get("/derived-books")
def list_derived_books(request: Request, limit: int = 50):
    own = owner(request)
    database = db()
    limit = max(1, min(limit, 200))
    with database.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM derived_books WHERE owner_id=%s ORDER BY updated_at DESC LIMIT %s", (own, limit))
            rows = cur.fetchall()
    return {"items": rows, "total": len(rows)}
