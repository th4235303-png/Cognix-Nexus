from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4
import json

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.ownership import get_book_for_request, owner_for_request
from app.services.embeddings import embedding_provider
from app.services.llm import llm_provider
from app.store import store

router = APIRouter(prefix="/brain", tags=["brain-vault-advanced"])


def _db():
    if store.database is None:
        raise HTTPException(status_code=503, detail="Persistent database is required for this feature")
    return store.database


def _require_unscoped_book_access(request: Request) -> None:
    owner_id = owner_for_request(request)
    if owner_id is None or store.database is None:
        return
    raise HTTPException(
        status_code=503,
        detail={
            "code": "OWNERSHIP_UNAVAILABLE",
            "message": "This book-wide feature is not scoped to an authenticated owner",
        },
    )


class SummaryCreate(BaseModel):
    book_id: str
    level: str = Field(pattern=r"^L[1-7]$")
    title: str | None = None
    content: str = Field(min_length=1)
    model: str | None = None
    source_ids: list[str] = Field(default_factory=list)


@router.post("/summaries", status_code=201)
def create_summary(payload: SummaryCreate, request: Request) -> dict:
    get_book_for_request(request, payload.book_id)
    db = _db()
    summary_id = f"SUM-{uuid4().hex[:8].upper()}"
    with db.connect() as conn:
        with conn.cursor() as cur:
            if payload.source_ids:
                cur.execute(
                    """SELECT count(*) AS total FROM chunks
                       WHERE id = ANY(%s)
                         AND chapter_id IN (SELECT id FROM chapters WHERE book_id=%s)""",
                    (payload.source_ids, payload.book_id),
                )
                if int(cur.fetchone()["total"]) != len(set(payload.source_ids)):
                    raise HTTPException(status_code=404, detail="Book evidence not found")
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
def list_summaries(book_id: str, request: Request) -> dict:
    get_book_for_request(request, book_id)
    db = _db()
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM book_summaries WHERE book_id=%s ORDER BY level, version DESC", (book_id,))
            items = cur.fetchall()
    return {"items": items, "total": len(items)}


class SummaryGenerationRequest(BaseModel):
    levels: list[str] = Field(default_factory=lambda: [f"L{i}" for i in range(1, 8)])


@router.post("/books/{book_id}/summaries/generate")
async def generate_book_summaries(book_id: str, payload: SummaryGenerationRequest, request: Request) -> dict:
    get_book_for_request(request, book_id)
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
def create_language_card(payload: LanguageCardCreate, request: Request) -> dict:
    owner_id = owner_for_request(request)
    db = _db()
    card_id = f"CARD-{uuid4().hex[:8].upper()}"
    return db.create_language_card(
        {
            "id": card_id,
            "front": payload.front,
            "back": payload.back,
            "language": payload.language,
            "source_note": payload.source_note,
        },
        owner_id,
    )


@router.get("/language/due")
def due_language_cards(request: Request, limit: int = 20) -> dict:
    owner_id = owner_for_request(request)
    db = _db()
    limit = max(1, min(limit, 100))
    items = db.list_language_cards_due_for_owner(owner_id, limit)
    return {"items": items, "total": len(items)}


@router.post("/language/cards/{card_id}/review")
def review_language_card(card_id: str, payload: LanguageReview, request: Request) -> dict:
    owner_id = owner_for_request(request)
    db = _db()
    updated = db.review_language_card(card_id, owner_id, payload.rating, _schedule)
    if updated is None:
        raise HTTPException(status_code=404, detail="Language card not found")
    return updated


class RetrievalRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=8, ge=1, le=30)
    rrf_k: int = Field(default=60, ge=1, le=200)


@router.post("/retrieval")
async def hybrid_retrieval(payload: RetrievalRequest, request: Request) -> dict:
    _require_unscoped_book_access(request)
    db = _db()
    if not embedding_provider.configured:
        raise HTTPException(status_code=503, detail="Semantic embeddings are not configured")

    vectors = await embedding_provider.embed([payload.query])
    query_vector = "[" + ",".join(str(float(value)) for value in vectors[0]) + "]"

    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH semantic AS (
                    SELECT c.id, c.chapter_id, c.sequence, c.page_number, c.content,
                           row_number() OVER (ORDER BY e.embedding_vector <=> %s::vector) AS rank
                    FROM embeddings e
                    JOIN chunks c ON c.id = e.owner_id
                    WHERE e.owner_type = 'chunk'
                      AND e.embedding_vector IS NOT NULL
                    ORDER BY e.embedding_vector <=> %s::vector
                    LIMIT %s
                ),
                lexical AS (
                    SELECT c.id, c.chapter_id, c.sequence, c.page_number, c.content,
                           row_number() OVER (
                               ORDER BY ts_rank_cd(c.search_vector, websearch_to_tsquery('simple', %s)) DESC,
                                        c.created_at DESC
                           ) AS rank
                    FROM chunks c
                    WHERE c.search_vector @@ websearch_to_tsquery('simple', %s)
                    ORDER BY ts_rank_cd(c.search_vector, websearch_to_tsquery('simple', %s)) DESC,
                             c.created_at DESC
                    LIMIT %s
                ),
                fused AS (
                    SELECT id, max(chapter_id) AS chapter_id, max(sequence) AS sequence,
                           max(page_number) AS page_number, max(content) AS content,
                           sum(rrf_score) AS rrf_score
                    FROM (
                        SELECT id, chapter_id, sequence, page_number, content,
                               1.0 / (%s + rank) AS rrf_score
                        FROM semantic
                        UNION ALL
                        SELECT id, chapter_id, sequence, page_number, content,
                               1.0 / (%s + rank) AS rrf_score
                        FROM lexical
                    ) ranked
                    GROUP BY id
                )
                SELECT id, chapter_id, sequence, page_number, content, rrf_score
                FROM fused
                ORDER BY rrf_score DESC, id
                LIMIT %s
                """,
                (
                    query_vector, query_vector, payload.limit,
                    payload.query, payload.query, payload.query, payload.limit,
                    payload.rrf_k, payload.rrf_k, payload.limit,
                ),
            )
            rows = cur.fetchall()

    return {
        "query": payload.query,
        "strategy": "hybrid_rrf",
        "semantic_enabled": True,
        "rrf_k": payload.rrf_k,
        "items": rows,
        "total": len(rows),
    }


class SynthesisCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    query: str = Field(min_length=1, max_length=2000)
    source_ids: list[str] = Field(default_factory=list)


@router.post("/synthesis", status_code=201)
def create_synthesis(payload: SynthesisCreate, request: Request) -> dict:
    _require_unscoped_book_access(request)
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
def get_synthesis(run_id: str, request: Request) -> dict:
    _require_unscoped_book_access(request)
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
async def generate_synthesis(run_id: str, payload: SynthesisGenerateRequest, request: Request) -> dict:
    _require_unscoped_book_access(request)
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
def put_vault_item(payload: VaultItem, request: Request) -> dict:
    db = _db()
    item_id = f"VAULT-{uuid4().hex[:8].upper()}"
    owner_id = owner_for_request(request)
    item = {
        "id": item_id,
        "label": payload.label,
        "ciphertext": payload.ciphertext,
        "nonce": payload.nonce,
        "kdf_salt": payload.kdf_salt,
        "kdf_params": payload.kdf_params,
    }
    row = db.save_vault_item(item, owner_id)
    if not row:
        raise HTTPException(status_code=409, detail="Vault item could not be created")
    return row


@router.get("/vault/items/{item_id}")
def get_vault_item(item_id: str, request: Request) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    item = db.get_vault_item_for_owner(item_id, owner_id)
    if not item:
        raise HTTPException(status_code=404, detail="Vault item not found")
    return item


@router.get("/vault/items")
def list_vault_items(request: Request) -> dict:
    db = _db()
    owner_id = owner_for_request(request)
    items = db.list_vault_items_for_owner(owner_id)
    return {"items": items, "total": len(items)}


class EmbedRequest(BaseModel):
    owner_type: str = Field(min_length=1, max_length=64)
    owner_ids: list[str] = Field(min_length=1, max_length=100)


@router.post("/embeddings/index")
async def index_embeddings(payload: EmbedRequest, request: Request) -> dict:
    _require_unscoped_book_access(request)
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
async def semantic_query(payload: SemanticQuery, request: Request) -> dict:
    _require_unscoped_book_access(request)
    db = _db()
    if not embedding_provider.configured:
        raise HTTPException(status_code=503, detail="Semantic embeddings are not configured")
    vector = (await embedding_provider.embed([payload.q]))[0]
    vector_literal = "[" + ",".join(str(float(v)) for v in vector) + "]"
    terms = [term for term in payload.q.lower().split() if term][:12]
    lexical_limit = min(50, max(payload.limit * 4, 12))
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT e.owner_id, e.content, e.model, "
                "1 - (e.embedding_vector <=> %s::vector) AS similarity, "
                "c.chapter_id, c.page_number, c.sequence "
                "FROM embeddings e JOIN chunks c ON c.id=e.owner_id "
                "WHERE e.embedding_vector IS NOT NULL AND e.owner_type='chunk' "
                "ORDER BY e.embedding_vector <=> %s::vector LIMIT %s",
                (vector_literal, vector_literal, lexical_limit),
            )
            semantic_rows = cur.fetchall()
            if terms:
                like_parts = []
                params = []
                for term in terms:
                    like_parts.append("lower(c.content) LIKE %s")
                    params.append("%" + term[:80] + "%")
                cur.execute(
                    "SELECT c.id AS owner_id, c.content, NULL::text AS model, "
                    "c.chapter_id, c.page_number, c.sequence "
                    "FROM chunks c WHERE " + " OR ".join(like_parts) +
                    " ORDER BY c.created_at DESC LIMIT %s",
                    (*params, lexical_limit),
                )
                lexical_rows = cur.fetchall()
            else:
                lexical_rows = []

    # Reciprocal Rank Fusion (D14): combine semantic and lexical evidence
    # without pretending either ranking is ground truth.
    fused: dict[str, dict] = {}
    k = 60
    for rank, row in enumerate(semantic_rows, start=1):
        item = fused.setdefault(row["owner_id"], {
            "chunk_id": row["owner_id"], "content": row["content"],
            "chapter_id": row["chapter_id"], "page_number": row["page_number"],
            "sequence": row["sequence"], "model": row.get("model"),
            "semantic_similarity": float(row["similarity"]),
            "semantic_rank": rank, "lexical_rank": None, "rrf_score": 0.0,
        })
        item["rrf_score"] += 1.0 / (k + rank)
    for rank, row in enumerate(lexical_rows, start=1):
        item = fused.setdefault(row["owner_id"], {
            "chunk_id": row["owner_id"], "content": row["content"],
            "chapter_id": row["chapter_id"], "page_number": row["page_number"],
            "sequence": row["sequence"], "model": row.get("model"),
            "semantic_similarity": None, "semantic_rank": None,
            "lexical_rank": rank, "rrf_score": 0.0,
        })
        item["lexical_rank"] = rank
        item["rrf_score"] += 1.0 / (k + rank)
    items = sorted(fused.values(), key=lambda item: item["rrf_score"], reverse=True)[:payload.limit]

    answer = None
    citations: list[str] = []
    message = "Evidence retrieved with hybrid semantic + lexical ranking. Configure COGNIX_LLM_API_URL and COGNIX_LLM_MODEL to enable cited answer synthesis."
    if llm_provider.configured and items:
        evidence = "\n\n".join(
            f"[chunk:{item['chunk_id']}] rrf={item['rrf_score']:.5f}\\n{item['content'][:5000]}"
            for item in items
        )
        answer = await llm_provider.complete(
            "Answer only from the supplied evidence. Do not invent facts. "
            "Cite every substantive statement with [chunk:ID]. If the evidence is insufficient, say so.",
            f"Question: {payload.q}\n\nEvidence:\n{evidence}",
        )
        citations = [item["chunk_id"] for item in items if f"[chunk:{item['chunk_id']}]" in answer]
        message = "Answer synthesized from hybrid retrieved evidence; citations identify supporting chunks."
    return {
        "query": payload.q,
        "mode": "hybrid_rrf_rag" if answer else "hybrid_rrf_evidence",
        "answer": answer,
        "citations": citations,
        "items": items,
        "total": len(items),
        "message": message,
    }


@router.get("/export")
def export_brain_vault(request: Request) -> dict:
    _require_unscoped_book_access(request)
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
def contradiction_candidates(request: Request, limit: int = 50) -> dict:
    _require_unscoped_book_access(request)
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
def review_contradiction(contradiction_id: str, payload: ContradictionReview, request: Request) -> dict:
    _require_unscoped_book_access(request)
    db = _db()
    with db.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE contradictions SET status=%s WHERE id=%s RETURNING *", (payload.status, contradiction_id))
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Contradiction candidate not found")
    return row
