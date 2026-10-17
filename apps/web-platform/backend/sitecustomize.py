"""Runtime compatibility defaults for the production Python process.

Supabase transaction-mode poolers do not support PostgreSQL prepared statements.
Psycopg 3 enables automatic prepared statements by default, so every connection
created by the backend pool must disable them when the application is routed
through a transaction pooler.
"""

from __future__ import annotations

from psycopg_pool import ConnectionPool as _ConnectionPool


class ConnectionPool(_ConnectionPool):
    """ConnectionPool with prepared statements disabled by default."""

    def __init__(self, *args, **kwargs):
        pool_kwargs = dict(kwargs.get("kwargs") or {})
        pool_kwargs.setdefault("prepare_threshold", None)
        kwargs["kwargs"] = pool_kwargs
        super().__init__(*args, **kwargs)
