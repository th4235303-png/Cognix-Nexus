from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4
import json

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.embeddings import embedding_provider
from app.services.llm import llm_provider
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


class SummaryGenerationRequest(BaseModel):
    levels: list[str] = Field(default_factory=lambda: [f"L{i}" for i in range(1, 8)])


@router.post("/books/{book_id}/summaries/generate")
async def generate_book_summaries(book_id: str, payload: SummaryGenerationRequest) -> dict:
    db = _db()
    levels = []
    for level in payload.levels:
        if level not in {f"L{i}" for i in range(1, 8)}:
            raise HTTPException(status_code=400, detail="levels must contain only L1-L7")
        if level not in levels:
            levels.append(level)
    if not levels:
        raise HTTPException(status_code=400, detail="At least one summary level is required")
    if not llm_provider.configured:
        raise HTTPException(status_code=503, detail="LLM synthesis is not configured")
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id,title,author FROM books WHERE id=%s", (book_id,))
            book = cur.fetchone()
            if not book:
                raise HTTPException(status_code=404, detail="Book not found")
            cur.execute(
                "SELECT id,chapter_id,content,page_number,sequence FROM chunks "
                "WHERE chapter_id IN (SELECT id FROM chapters WHERE book_id=%s) "
                "ORDER BY chapter_id,sequence LIMIT 120",
                (book_id,),
            )
            chunks = cur.fetchall()
            cur.execute(
                "SELECT level,content FROM book_summaries WHERE book_id=%s ORDER BY level,version DESC",
                (book_id,),
            )
            existing = cur.fetchall()
    evidence = "\n\n".join(
        f"[chunk:{row['id']}] chapter={row['chapter_id']} page={row['page_number']}\n{row['content'][:3500]}"
        for row in chunks
    )
    prior = {row["level"]: row["content"] for row in existing}
    generated = []
    level_instructions = {
        "L1": "Write a one-sentence essence of the whole book.",
        "L2": "Write a concise executive overview: thesis, scope, and major conclusions.",
        "L3": "Map the book's major chapters or sections and what each contributes.",
        "L4": "Extract the central concepts, definitions, and relationships.",
        "L5": "Explain the important mechanisms, arguments, methods, or causal chains.",
        "L6": "Identify limitations, assumptions, open questions, disagreements, and evidence gaps.",
        "L7": "Produce a durable synthesis connecting the book's ideas while preserving uncertainty.",
    }
    for level in levels:
        previous = "\n\n".join(f"{k}: {v[:5000]}" for k, v in prior.items()) if prior else ""
        prompt = (
            f"Book: {book['title']} by {book.get('author') or 'Unknown'}\n"
            f"Task: {level_instructions[level]}\n"
            "Every factual claim must be traceable to supplied chunks. "
            "Use [chunk:ID] citations inline. Do not invent content."
            f"\n\nSource chunks:\n{evidence}\nPrior levels:\n{previous}"
        )
        content = await llm_provider.complete(
            "You are a research summarizer. Preserve evidence boundaries and uncertainty.",
            prompt,
        )
        source_ids = [row["id"] for row in chunks if f"[chunk:{row['id']}]" in content]
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COALESCE(MAX(version),0)+1 AS version FROM book_summaries WHERE book_id=%s AND level=%s",
                    (book_id, level),
                )
                version = int(cur.fetchone()["version"])
                summary_id = f"SUM-{uuid4().hex[:8].upper()}"
                cur.execute(
                    "INSERT INTO book_summaries(id,book_id,level,title,content,version,model) VALUES(%s,%s,%s,%s,%s,%s,%s)",
                    (summary_id, book_id, level, level, content, version, llm_provider.model),
                )
                for source_id in source_ids:
                    cur.execute(
                        "INSERT INTO summary_sources(summary_id,source_type,source_id) VALUES(%s,%s,%s) ON CONFLICT DO NOTHING",
                        (summary_id, "chunk", source_id),
                    )
            conn.commit()
        prior[level] = content
        generated.append({"id": summary_id, "level": level, "version": version, "content": content, "source_ids": source_ids})
    return {"book_id": book_id, "model": llm_provider.model, "items": generated}


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
    source_ids: list[str] = Field(default_factory=list)


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
                (run_id, payload.title, payload.query, json.dumps(payload.source_ids), "evidence_only"),
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



class SynthesisGenerateRequest(BaseModel):
    limit: int = Field(default=12, ge=1, le=30)


@router.post("/synthesis/{run_id}/generate")
async def generate_synthesis(run_id: str, payload: SynthesisGenerateRequest) -> dict:
    db = _db()
    if not llm_provider.configured:
        raise HTTPException(status_code=503, detail="LLM synthesis is not configured")
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM synthesis_runs WHERE id=%s FOR UPDATE", (run_id,))
            run = cur.fetchone()
            if not run:
                raise HTTPException(status_code=404, detail="Synthesis run not found")
            source_ids = run.get("source_ids") or []
            if isinstance(source_ids, str):
                source_ids = json.loads(source_ids)
            if source_ids:
                cur.execute("SELECT id,content FROM chunks WHERE id=ANY(%s) ORDER BY id LIMIT %s", (source_ids, payload.limit))
            else:
                terms = [term for term in run["query"].lower().split() if term][:8]
                pattern = "%" + "%".join(terms) + "%" if terms else "%"
                cur.execute("SELECT id,content FROM chunks WHERE lower(content) LIKE %s ORDER BY created_at DESC LIMIT %s", (pattern, payload.limit))
            rows = cur.fetchall()
    evidence = "\n\n".join(f"[chunk:{row['id']}]\n{row['content'][:5000]}" for row in rows)
    if not evidence:
        raise HTTPException(status_code=404, detail="No evidence found for synthesis")
    answer = await llm_provider.complete(
        "Synthesize only from supplied evidence. Keep disagreements explicit and cite every substantive claim with [chunk:ID].",
        f"Research question: {run['query']}\n\nEvidence:\n{evidence}",
    )
    citations = [row["id"] for row in rows if f"[chunk:{row['id']}]" in answer]
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE synthesis_runs SET result=%s,citations=%s::jsonb,status=%s WHERE id=%s RETURNING *", (answer, json.dumps(citations), "completed", run_id))
            updated = cur.fetchone()
        conn.commit()
    return updated


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


class EmbedRequest(BaseModel):
    owner_type: str = Field(min_length=1, max_length=64)
    owner_ids: list[str] = Field(min_length=1, max_length=100)


@router.post("/embeddings/index")
async def index_embeddings(payload: EmbedRequest) -> dict:
    db = _db()
    if not embedding_provider.configured:
        raise HTTPException(status_code=503, detail="Semantic embeddings are not configured")
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, content FROM chunks WHERE id = ANY(%s) ORDER BY id",
                (payload.owner_ids,),
            )
            rows = cur.fetchall()
    if not rows:
        return {"indexed": 0}
    vectors = await embedding_provider.embed([row["content"] for row in rows])
    with db.connect() as conn:
        with conn.cursor() as cur:
            for row, vector in zip(rows, vectors):
                cur.execute(
                    "INSERT INTO embeddings(id,owner_type,owner_id,content,embedding,model,created_at,embedding_vector) "
                    "VALUES(%s,%s,%s,%s,%s,%s,now(),%s::vector) "
                    "ON CONFLICT(owner_type,owner_id) DO UPDATE SET content=EXCLUDED.content,embedding=EXCLUDED.embedding,model=EXCLUDED.model,embedding_vector=EXCLUDED.embedding_vector",
                    (
                        f"EMB-{row['id']}",
                        payload.owner_type,
                        row["id"],
                        row["content"],
                        json.dumps(vector),
                        embedding_provider.model,
                        "[" + ",".join(str(float(v)) for v in vector) + "]",
                    ),
                )
        conn.commit()
    return {"indexed": len(rows), "model": embedding_provider.model}


class SemanticQuery(BaseModel):
    q: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=8, ge=1, le=30)


@router.post("/query/semantic")
async def semantic_query(payload: SemanticQuery) -> dict:
    db = _db()
    if not embedding_provider.configured:
        raise HTTPException(status_code=503, detail="Semantic embeddings are not configured")
    vector = (await embedding_provider.embed([payload.q]))[0]
    vector_literal = "[" + ",".join(str(float(v)) for v in vector) + "]"
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT e.owner_id, e.content, e.model, 1 - (e.embedding_vector <=> %s::vector) AS similarity, "
                "c.chapter_id, c.page_number, c.sequence "
                "FROM embeddings e JOIN chunks c ON c.id=e.owner_id "
                "WHERE e.embedding_vector IS NOT NULL AND e.owner_type='chunk' "
                "ORDER BY e.embedding_vector <=> %s::vector LIMIT %s",
                (vector_literal, vector_literal, payload.limit),
            )
            rows = cur.fetchall()
    items = [
        {
            "chunk_id": row["owner_id"],
            "content": row["content"],
            "similarity": float(row["similarity"]),
            "chapter_id": row["chapter_id"],
            "page_number": row["page_number"],
            "sequence": row["sequence"],
            "model": row["model"],
        }
        for row in rows
    ]
    answer = None
    citations: list[str] = []
    message = "Evidence retrieved. Configure COGNIX_LLM_API_URL and COGNIX_LLM_MODEL to enable cited answer synthesis."
    if llm_provider.configured and items:
        evidence = "\n\n".join(
            f"[chunk:{item['chunk_id']}] similarity={item['similarity']:.3f}\n{item['content'][:5000]}"
            for item in items
        )
        answer = await llm_provider.complete(
            "Answer only from the supplied evidence. Do not invent facts. "
            "Cite every substantive statement with [chunk:ID]. If the evidence is insufficient, say so.",
            f"Question: {payload.q}\n\nEvidence:\n{evidence}",
        )
        citations = [item["chunk_id"] for item in items if f"[chunk:{item['chunk_id']}]" in answer]
        message = "Answer synthesized from retrieved evidence; citations identify the supporting chunks."
    return {
        "query": payload.q,
        "mode": "semantic_rag" if answer else "semantic_evidence",
        "answer": answer,
        "citations": citations,
        "items": items,
        "message": message,
    }


@router.get("/export")
def export_brain_vault() -> dict:
    db = _db()
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM books ORDER BY created_at")
            books = cur.fetchall()
            cur.execute("SELECT * FROM chapters ORDER BY book_id, chapter_number")
            chapters = cur.fetchall()
            cur.execute("SELECT id,title,content,note_type,status,created_at,updated_at FROM notes ORDER BY updated_at DESC")
            notes = cur.fetchall()
            cur.execute("SELECT * FROM concepts ORDER BY name")
            concepts = cur.fetchall()
            cur.execute("SELECT * FROM concept_links ORDER BY created_at")
            links = cur.fetchall()
            cur.execute("SELECT * FROM book_summaries ORDER BY book_id, level, version")
            summaries = cur.fetchall()
    return {
        "format": "cognix-brain-vault-json",
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "books": books,
        "chapters": chapters,
        "notes": notes,
        "concepts": concepts,
        "concept_links": links,
        "summaries": summaries,
    }


@router.get("/contradictions/candidates")
def contradiction_candidates(limit: int = 50) -> dict:
    db = _db()
    limit = max(1, min(limit, 100))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.id AS left_id, b.id AS right_id, a.content AS left_content, b.content AS right_content
                FROM chunks a
                JOIN chunks b ON a.id < b.id
                WHERE (
                    lower(a.content) LIKE '%%not %%' OR lower(a.content) LIKE '%%no %%' OR
                    lower(a.content) LIKE '%%never %%' OR lower(a.content) LIKE '%%cannot %%'
                )
                AND (
                    lower(b.content) NOT LIKE '%%not %%' AND lower(b.content) NOT LIKE '%%no %%' AND
                    lower(b.content) NOT LIKE '%%never %%' AND lower(b.content) NOT LIKE '%%cannot %%'
                )
                ORDER BY a.created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    items = []
    with db.connect() as conn:
        with conn.cursor() as cur:
            for row in rows:
                candidate_id = "CONTR-" + sha256(f"{row['left_id']}:{row['right_id']}".encode()).hexdigest()[:16].upper()
                cur.execute(
                    "INSERT INTO contradictions(id,left_source_type,left_source_id,right_source_type,right_source_id,statement,status) VALUES(%s,'chunk',%s,'chunk',%s,%s,'needs_review') ON CONFLICT (id) DO NOTHING",
                    (candidate_id, row["left_id"], row["right_id"], "Potential contradiction candidate; human review required."),
                )
                items.append({
                    "id": candidate_id,
                    "left_chunk_id": row["left_id"],
                    "right_chunk_id": row["right_id"],
                    "left_content": row["left_content"],
                    "right_content": row["right_content"],
                    "status": "needs_review",
                })
        conn.commit()
    return {
        "mode": "candidate_detection",
        "message": "Candidates require human review; this endpoint does not assert that a contradiction is true.",
        "items": items,
    }


class ContradictionReview(BaseModel):
    status: str = Field(pattern=r"^(confirmed|rejected|needs_review)$")


@router.post("/contradictions/{contradiction_id}/review")
def review_contradiction(contradiction_id: str, payload: ContradictionReview) -> dict:
    db = _db()
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE contradictions SET status=%s WHERE id=%s RETURNING *", (payload.status, contradiction_id))
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Contradiction candidate not found")
    return row
