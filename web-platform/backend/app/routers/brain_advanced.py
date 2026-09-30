from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.store import store

router = APIRouter(prefix="/brain", tags=["brain-vault-advanced"])


def _db():
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required for this feature")
    return store.database


class SummaryCreate(BaseModel):
    book_id: str
    level: str = Field(pattern=r"^L[1-7]$")
    title: str | None = None
    content: str = Field(min_length=1)
    model: str | None = None
    source_ids: list[str] = Field(default_factory=list)


@router.post("/summaries", status_code=201)
def create_summary(payload: SummaryCreate) -> dict:
    db = _db()
    summary_id = f"SUM-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(version), 0) + 1 AS version FROM book_summaries WHERE book_id=%s AND level=%s", (payload.book_id, payload.level))
            version = int(cur.fetchone()["version"])
            cur.execute(
                "INSERT INTO book_summaries(id,book_id,level,title,content,version,model) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                (summary_id, payload.book_id, payload.level, payload.title, payload.content, version, payload.model),
            )
            for source_id in payload.source_ids:
                cur.execute(
                    "INSERT INTO summary_sources(summary_id,source_type,source_id) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING",
                    (summary_id, "chunk", source_id),
                )
        conn.commit()
    return {"id": summary_id, "book_id": payload.book_id, "level": payload.level, "version": version, "content": payload.content}


@router.get("/books/{book_id}/summaries")
def list_summaries(book_id: str) -> dict:
    db = _db()
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM book_summaries WHERE book_id=%s ORDER BY level, version DESC", (book_id,))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


class LanguageCardCreate(BaseModel):
    front: str = Field(min_length=1, max_length=1000)
    back: str = Field(min_length=1, max_length=2000)
    language: str = Field(min_length=2, max_length=32)
    source_note: str | None = None


class LanguageReview(BaseModel):
    rating: int = Field(ge=1, le=4)


def _schedule(card: dict, rating: int) -> tuple[float, float, int, int, str, datetime]:
    stability = float(card["stability"])
    difficulty = float(card["difficulty"])
    reps = int(card["reps"])
    lapses = int(card["lapses"])
    if rating == 1:
        lapses += 1
        reps = 0
        stability = max(0.5, stability * 0.35)
        state = "relearning"
        days = 0.25
    else:
        reps += 1
        difficulty = min(10.0, max(1.0, difficulty + (3 - rating) * 0.4))
        gain = {2: 1.15, 3: 1.65, 4: 2.35}[rating]
        stability = max(1.0, stability * gain + 0.5)
        state = "review" if reps >= 2 else "learning"
        days = max(0.2, min(180.0, stability * (1.0 + (rating - 2) * 0.25)))
    due = datetime.now(timezone.utc) + timedelta(days=days)
    return stability, difficulty, reps, lapses, state, due


@router.post("/language/cards", status_code=201)
def create_language_card(payload: LanguageCardCreate) -> dict:
    db = _db()
    card_id = f"CARD-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO language_cards(id,front,back,language,source_note) VALUES(%s,%s,%s,%s,%s) RETURNING *",
                (card_id, payload.front, payload.back, payload.language, payload.source_note),
            )
            row = cur.fetchone()
        conn.commit()
    return row


@router.get("/language/due")
def due_language_cards(limit: int = 20) -> dict:
    db = _db()
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM language_cards WHERE due_at <= now() ORDER BY due_at LIMIT %s", (limit,))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


@router.post("/language/cards/{card_id}/review")
def review_language_card(card_id: str, payload: LanguageReview) -> dict:
    db = _db()
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM language_cards WHERE id=%s FOR UPDATE", (card_id,))
            card = cur.fetchone()
            if not card:
                raise HTTPException(status_code=404, detail="Language card not found")
            stability, difficulty, reps, lapses, state, due = _schedule(card, payload.rating)
            cur.execute(
                "UPDATE language_cards SET stability=%s,difficulty=%s,reps=%s,lapses=%s,state=%s,due_at=%s,updated_at=now() WHERE id=%s RETURNING *",
                (stability, difficulty, reps, lapses, state, due, card_id),
            )
            updated = cur.fetchone()
            cur.execute(
                "INSERT INTO language_reviews(id,card_id,rating,scheduled_for) VALUES(%s,%s,%s,%s)",
                (f"REV-{uuid4().hex[:8].upper()}", card_id, payload.rating, due),
            )
        conn.commit()
    return updated


class SynthesisCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    query: str = Field(min_length=1, max_length=2000)
    source_ids: list[str] = []


@router.post("/synthesis", status_code=201)
def create_synthesis(payload: SynthesisCreate) -> dict:
    # Evidence collection is deliberately separated from generation. No AI text
    # is invented here; a later model provider may consume this evidence package.
    db = _db()
    run_id = f"SYN-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO synthesis_runs(id,title,query,source_ids,status) VALUES(%s,%s,%s,%s::jsonb,%s) RETURNING *",
                (run_id, payload.title, payload.query, str(json.dumps(payload.source_ids), "evidence_only"),
            )
            row = cur.fetchone()
        conn.commit()
    return row


@router.get("/synthesis/{run_id}")
def get_synthesis(run_id: str) -> dict:
    db = _db()
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM synthesis_runs WHERE id=%s", (run_id,))
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Synthesis run not found")
    return row


class VaultItem(BaseModel):
    label: str = Field(min_length=1, max_length=300)
    ciphertext: str = Field(min_length=1)
    nonce: str = Field(min_length=1)
    kdf_salt: str = Field(min_length=1)
    kdf_params: dict


@router.post("/vault/items", status_code=201)
def put_vault_item(payload: VaultItem) -> dict:
    db = _db()
    item_id = f"VAULT-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO vault_items(id,label,ciphertext,nonce,kdf_salt,kdf_params) VALUES(%s,%s,%s,%s,%s,%s) RETURNING id,label,nonce,kdf_salt,kdf_params,created_at,updated_at",
                (item_id, payload.label, payload.ciphertext, payload.nonce, payload.kdf_salt, payload.kdf_params),
            )
            row = cur.fetchone()
        conn.commit()
    return row


@router.get("/vault/items")
def list_vault_items() -> dict:
    db = _db()
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id,label,nonce,kdf_salt,kdf_params,created_at,updated_at FROM vault_items ORDER BY updated_at DESC")
            items = cur.fetchall()
    return {"items": items, "total": len(items)}
