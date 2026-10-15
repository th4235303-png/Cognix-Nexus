from contextvars import ContextVar, Token

_REQUEST_OWNER: ContextVar[str | None] = ContextVar("cognix_request_owner", default=None)


def set_request_owner(owner_id: str | None) -> Token:
    return _REQUEST_OWNER.set(owner_id)


def reset_request_owner(token: Token) -> None:
    _REQUEST_OWNER.reset(token)


def current_request_owner() -> str | None:
    return _REQUEST_OWNER.get()
