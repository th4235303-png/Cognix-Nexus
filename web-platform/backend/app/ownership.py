import os
from contextvars import ContextVar, Token

from fastapi import HTTPException, Request

from app.store import store

_REQUEST_OWNER: ContextVar[str | None] = ContextVar("cognix_request_owner", default=None)


def set_request_owner(owner_id: str | None) -> Token:
    return _REQUEST_OWNER.set(owner_id)


def reset_request_owner(token: Token) -> None:
    _REQUEST_OWNER.reset(token)


def current_request_owner() -> str | None:
    return _REQUEST_OWNER.get()


def owner_for_request(request: Request) -> str | None:
    auth = getattr(request.state, "auth", None)
    subject = auth.get("sub") if isinstance(auth, dict) else None
    if subject == "anonymous":
        if os.getenv("COGNIX_DEV_MODE", "").strip().lower() in {"1", "true", "yes", "on"}:
            return None
        raise HTTPException(status_code=401, detail={"code": "AUTH_REQUIRED", "message": "Authenticated identity is required"})
    if not isinstance(subject, str) or not subject.strip():
        raise HTTPException(status_code=401, detail={"code": "INVALID_IDENTITY", "message": "Authenticated identity is required"})
    return subject


def get_source_for_request(request: Request, source_id: str) -> dict:
    source = store.get_source_for_owner(source_id, owner_for_request(request))
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


def get_task_for_request(request: Request, task_id: str) -> dict:
    task = store.get_task_for_owner(task_id, owner_for_request(request))
    if task is None:
        raise HTTPException(status_code=404, detail="Processing task not found")
    return task


def get_book_for_request(request: Request, book_id: str) -> dict:
    owner_id = owner_for_request(request)
    book = store.get_brain_book_for_owner(book_id, owner_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book
