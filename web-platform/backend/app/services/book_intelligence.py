from __future__ import annotations

import json
import logging
from uuid import uuid4

from app.services.llm import llm_provider
from app.store import store

logger = logging.getLogger("cognix.book_intelligence")


def parse_json(text: str) -> dict:
    try:
        data = json.loads(text.strip())
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def values(data: dict, key: str) -> list[str]:
    value = data.get(key, [])
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return [str(v).strip() for v in value if str(v).strip()][:20] if isinstance(value, list) else []


async def read_ai(system: str, prompt: str) -> dict:
    raw = await llm_provider.complete(system, prompt)
    return parse_json(raw) or {"summary": raw, "keys": [], "principles": [], "lessons": [], "definitions": [], "examples": [], "caveats": []}


async def advance_book_ai(limit: int = 1) -> int:
    db = store.database
    if db is None or not llm_provider.configured:
        return 0
    done = 0
    for _ in range(max(1, limit)):
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT b.id,b.title,b.author,b.category FROM books b JOIN book_reading_progress p ON p.book_id=b.id "
                    "WHERE b.status='processing' AND b.processing_stage='ai_reading' "
                    "AND p.status IN ('queued','running') AND (p.claimed_at IS NULL OR p.claimed_at < now()-interval '20 minutes') "
                    "ORDER BY p.updated_at LIMIT 1 FOR UPDATE SKIP LOCKED"
                )
                book = cur.fetchone()
                if not book:
                    break
                token = uuid4().hex
                cur.execute(
                    "UPDATE book_reading_progress SET status='running',claim_token=%s,claimed_at=now(),"
                    "started_at=COALESCE(started_at,now()),updated_at=now() WHERE book_id=%s",
                    (token, book["id"]),
                )
            conn.commit()

        try:
            with db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT ch.id,ch.chapter_number,ch.title FROM chapters ch "
                        "WHERE ch.book_id=%s AND NOT EXISTS "
                        "(SELECT 1 FROM chapter_summaries cs WHERE cs.chapter_id=ch.id AND cs.status='final') "
                        "ORDER BY ch.chapter_number LIMIT 1",
                        (book["id"],),
                    )
                    chapter = cur.fetchone()
                    if chapter:
                        cur.execute("SELECT id,content,page_number FROM chunks WHERE chapter_id=%s ORDER BY sequence", (chapter["id"],))
                        chunks = cur.fetchall()
                    else:
                        cur.execute("SELECT id,content FROM chapter_summaries WHERE book_id=%s ORDER BY created_at", (book["id"],))
                        summaries = cur.fetchall()

            if chapter:
                evidence = "\n\n".join(
                    "[chunk:%s] page=%s\n%s" % (c["id"], c["page_number"], c["content"][:5000])
                    for c in chunks
                )
                data = await read_ai(
                    "You are Cognix background book reader. Return JSON only with summary, keys, principles, lessons, definitions, examples and caveats. Never invent facts.",
                    "Book: %s\nCategory: %s\nChapter %s: %s\n%s"
                    % (book["title"], book["category"], chapter["chapter_number"], chapter["title"], evidence),
                )
                summary = str(data.get("summary") or "").strip()
                if not summary:
                    raise RuntimeError("AI reader returned no chapter summary")
                source_ids = [c["id"] for c in chunks]
                with db.connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COALESCE(MAX(version),0)+1 AS v FROM chapter_summaries WHERE chapter_id=%s", (chapter["id"],))
                        version = int(cur.fetchone()["v"])
                        cur.execute(
                            "INSERT INTO chapter_summaries(id,book_id,chapter_id,owner_id,status,content,version,model,source_chunk_ids) "
                            "VALUES(%s,%s,%s,(SELECT owner_id FROM books WHERE id=%s),'final',%s,%s,%s,%s::jsonb)",
                            (f"CHSUM-{uuid4().hex[:8].upper()}", book["id"], chapter["id"], book["id"], summary, version, llm_provider.model, json.dumps(source_ids)),
                        )
                        for kind in ("keys", "principles", "lessons", "definitions", "examples", "caveats"):
                            for item in values(data, kind):
                                cur.execute(
                                    "INSERT INTO knowledge_items(id,book_id,chapter_id,owner_id,category,knowledge_type,title,content,confidence,status,model,source_chunk_ids) "
                                    "VALUES(%s,%s,%s,(SELECT owner_id FROM books WHERE id=%s),%s,%s,%s,%s,0.8,'draft',%s,%s::jsonb)",
                                    (f"KN-{uuid4().hex[:8].upper()}", book["id"], chapter["id"], book["id"], book["category"], kind, chapter["title"], item, llm_provider.model, json.dumps(source_ids)),
                                )
                        cur.execute(
                            "UPDATE book_reading_progress SET completed_units=completed_units+1,"
                            "total_units=(SELECT count(*) FROM chapters WHERE book_id=%s),"
                            "percent=round((completed_units+1)*100.0/GREATEST((SELECT count(*) FROM chapters WHERE book_id=%s),1),2),"
                            "current_chapter_id=%s,current_chapter_number=%s,last_checkpoint_at=now(),updated_at=now(),"
                            "claim_token=NULL,claimed_at=NULL,status='running',paused_reason=NULL WHERE book_id=%s AND claim_token=%s",
                            (book["id"], book["id"], chapter["id"], chapter["chapter_number"], book["id"], token),
                        )
                        cur.execute(
                            "INSERT INTO reading_events(id,book_id,owner_id,event_type,stage,percent,chapter_id,chapter_number,message,metadata) "
                            "SELECT %s,owner_id,'chapter_completed','ai_reading',percent,%s,%s,'Chapter completed',%s::jsonb "
                            "FROM books JOIN book_reading_progress ON book_reading_progress.book_id=books.id WHERE books.id=%s",
                            (f"EV-{uuid4().hex[:8].upper()}", chapter["id"], chapter["chapter_number"], json.dumps({"model": llm_provider.model}), book["id"]),
                        )
                    conn.commit()
                done += 1
            else:
                evidence = "\n\n".join("[chapter:%s] %s" % (s["id"], s["content"][:7000]) for s in summaries)
                data = await read_ai(
                    "You are Cognix final book synthesizer. Return JSON only with summary, keys, principles and lessons. Preserve disagreement and source boundaries.",
                    "Book: %s\nCategory: %s\n%s" % (book["title"], book["category"], evidence),
                )
                final = str(data.get("summary") or "").strip()
                if not final:
                    raise RuntimeError("AI reader returned no final book synthesis")
                with db.connect() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COALESCE(MAX(version),0)+1 AS v FROM book_summaries WHERE book_id=%s AND level='L7'", (book["id"],))
                        version = int(cur.fetchone()["v"])
                        summary_id = f"SUM-{uuid4().hex[:8].upper()}"
                        cur.execute(
                            "INSERT INTO book_summaries(id,book_id,level,title,content,version,model) VALUES(%s,%s,'L7',%s,%s,%s,%s)",
                            (summary_id, book["id"], book["title"] + " — final synthesis", final, version, llm_provider.model),
                        )
                        cur.execute(
                            "INSERT INTO summary_sources(summary_id,source_type,source_id) "
                            "SELECT %s,'chapter_summary',id FROM chapter_summaries WHERE book_id=%s",
                            (summary_id, book["id"]),
                        )
                        for kind in ("keys", "principles", "lessons"):
                            for item in values(data, kind):
                                cur.execute(
                                    "INSERT INTO knowledge_items(id,book_id,owner_id,category,knowledge_type,title,content,confidence,status,model) "
                                    "VALUES(%s,%s,(SELECT owner_id FROM books WHERE id=%s),%s,%s,%s,%s,0.85,'draft',%s)",
                                    (f"KN-{uuid4().hex[:8].upper()}", book["id"], book["id"], book["category"], kind, book["title"], item, llm_provider.model),
                                )
                        cur.execute(
                            "UPDATE books SET status='ready',processing_stage='completed',processed_at=now(),"
                            "ai_reading_paused_reason=NULL,updated_at=now() WHERE id=%s",
                            (book["id"],),
                        )
                        cur.execute(
                            "UPDATE book_reading_progress SET status='completed',stage='completed',completed_units=total_units,"
                            "percent=100,completed_at=now(),last_checkpoint_at=now(),claim_token=NULL,claimed_at=NULL,updated_at=now() "
                            "WHERE book_id=%s AND claim_token=%s",
                            (book["id"], token),
                        )
                        cur.execute(
                            "INSERT INTO reading_events(id,book_id,owner_id,event_type,stage,percent,message) "
                            "SELECT %s,owner_id,'book_completed','completed',100,'Book AI reading completed' FROM books WHERE id=%s",
                            (f"EV-{uuid4().hex[:8].upper()}", book["id"]),
                        )
                    conn.commit()
                done += 1
        except Exception as exc:
            with db.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE book_reading_progress SET status='queued',paused_reason=%s,claim_token=NULL,claimed_at=NULL,updated_at=now() "
                        "WHERE book_id=%s AND claim_token=%s",
                        (type(exc).__name__, book["id"], token),
                    )
                    cur.execute("UPDATE books SET ai_reading_paused_reason=%s,updated_at=now() WHERE id=%s", (type(exc).__name__, book["id"]))
                conn.commit()
            logger.warning("book_ai_reading_paused book_id=%s error_type=%s", book["id"], type(exc).__name__)
    return done
