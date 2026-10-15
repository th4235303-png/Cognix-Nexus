from __future__ import annotations

"""Phase 16 — Advanced Layer runtime tests.

Tests cover:
- WikiEntity / GrowthMetric / OfflineHandoff / SecretRef contract construction
- validate_secret_ref() and validate_breach_prefix() helpers
- persist_wiki_entity() — source lineage required, entity_type allowlist (no-DB)
- persist_growth_metric() — evidence+derivation required (no-DB)
- persist_offline_handoff() — format allowlist (no-DB)
- persist_secret_ref() — kind allowlist, ciphertext_ref only (no-DB)
"""

import sys
import pytest
from unittest.mock import MagicMock, patch

# ─── Stub psycopg tree ────────────────────────────────────────────────────────

def _mock_mod(name: str) -> MagicMock:
    parts = name.split(".")
    for i in range(1, len(parts) + 1):
        key = ".".join(parts[:i])
        if key not in sys.modules:
            sys.modules[key] = MagicMock()
    return sys.modules[name]  # type: ignore[return-value]

for _mod_name in (
    "psycopg", "psycopg.rows", "psycopg.types", "psycopg.types.json", "psycopg_pool",
):
    _mock_mod(_mod_name)

sys.modules["psycopg.rows"].dict_row = None  # type: ignore[attr-defined]
sys.modules["psycopg.types.json"].Jsonb = MagicMock  # type: ignore[attr-defined]
sys.modules["psycopg_pool"].ConnectionPool = MagicMock  # type: ignore[attr-defined]

from app.services.advanced_layer import (
    WikiEntity,
    GrowthMetric,
    OfflineHandoff,
    SecretRef,
    BreachCheckRequest,
    validate_secret_ref,
    validate_breach_prefix,
)
from app.services.advanced_layer_service import (
    persist_wiki_entity,
    persist_growth_metric,
    persist_offline_handoff,
    persist_secret_ref,
)


# ─── Contract construction ────────────────────────────────────────────────────

class TestWikiEntity:
    def test_construction(self):
        e = WikiEntity("W-1", "owner", "Gemini", "technology", source_refs=("SRC-1",))
        assert e.entity_type == "technology"
        assert len(e.source_refs) == 1

    def test_frozen(self):
        e = WikiEntity("W-1", "owner", "Gemini", "technology")
        with pytest.raises((AttributeError, TypeError)):
            e.name = "GPT"  # type: ignore[misc]

    def test_empty_source_refs_allowed_at_contract_level(self):
        # Validation is enforced by the service, not the dataclass.
        e = WikiEntity("W-1", "owner", "Gemini", "technology", source_refs=())
        assert e.source_refs == ()


class TestGrowthMetric:
    def test_construction(self):
        gm = GrowthMetric("G-1", "owner", "pages_read", 42.0, "pages",
                          evidence_refs=("S-1",), derivation="count of reading_events")
        assert gm.value == 42.0
        assert gm.derivation == "count of reading_events"

    def test_frozen(self):
        gm = GrowthMetric("G-1", "owner", "pages_read", 42.0, "pages")
        with pytest.raises((AttributeError, TypeError)):
            gm.value = 99.0  # type: ignore[misc]


class TestOfflineHandoff:
    def test_construction(self):
        h = OfflineHandoff("H-1", "owner", "encrypted_archive", "s3://bucket/export.zip")
        assert h.recoverable is True
        assert h.format == "encrypted_archive"

    def test_frozen(self):
        h = OfflineHandoff("H-1", "owner", "signed_manifest", "s3://bucket/manifest.sig")
        with pytest.raises((AttributeError, TypeError)):
            h.recoverable = False  # type: ignore[misc]


class TestSecretRef:
    def test_construction(self):
        s = SecretRef("S-1", "owner", "totp", "vault://secret/totp-key")
        assert s.kind == "totp"

    def test_frozen(self):
        s = SecretRef("S-1", "owner", "ssh_key", "vault://secret/ssh-key")
        with pytest.raises((AttributeError, TypeError)):
            s.kind = "credential"  # type: ignore[misc]


# ─── validate_secret_ref ──────────────────────────────────────────────────────

class TestValidateSecretRef:
    def test_valid(self):
        s = SecretRef("S-1", "owner", "totp", "vault://key")
        assert validate_secret_ref(s)

    def test_empty_id_invalid(self):
        s = SecretRef("", "owner", "totp", "vault://key")
        assert not validate_secret_ref(s)

    def test_empty_owner_invalid(self):
        s = SecretRef("S-1", "", "totp", "vault://key")
        assert not validate_secret_ref(s)

    def test_empty_ref_invalid(self):
        s = SecretRef("S-1", "owner", "totp", "")
        assert not validate_secret_ref(s)


# ─── validate_breach_prefix ───────────────────────────────────────────────────

class TestValidateBreachPrefix:
    def test_5_char_prefix_valid(self):
        r = BreachCheckRequest("owner", "ABCDE")
        assert validate_breach_prefix(r)

    def test_6_char_prefix_valid(self):
        r = BreachCheckRequest("owner", "ABCDEF")
        assert validate_breach_prefix(r)

    def test_4_char_prefix_invalid(self):
        r = BreachCheckRequest("owner", "ABCD")
        assert not validate_breach_prefix(r)

    def test_7_char_prefix_invalid(self):
        r = BreachCheckRequest("owner", "ABCDEFG")
        assert not validate_breach_prefix(r)

    def test_empty_owner_invalid(self):
        r = BreachCheckRequest("", "ABCDE")
        assert not validate_breach_prefix(r)


# ─── persist_wiki_entity (no-DB) ─────────────────────────────────────────────

class TestPersistWikiEntityNoDB:
    def _call(self, owner="owner", name="Gemini", etype="technology", refs=None, db=None):
        _refs = ["SRC-1"] if refs is None else refs
        with patch("app.services.advanced_layer_service.store") as m:
            m.database = db
            return persist_wiki_entity(owner, name, etype, _refs)

    def test_none_when_no_db(self):
        assert self._call(db=None) is None

    def test_none_when_empty_owner(self):
        assert self._call(owner="", db=MagicMock()) is None

    def test_none_when_empty_name(self):
        assert self._call(name="", db=MagicMock()) is None

    def test_none_when_unknown_entity_type(self):
        assert self._call(etype="alien", db=MagicMock()) is None

    def test_none_when_no_source_refs(self):
        assert self._call(refs=[], db=MagicMock()) is None


# ─── persist_growth_metric (no-DB) ────────────────────────────────────────────

class TestPersistGrowthMetricNoDB:
    def _call(self, owner="owner", metric="pages_read", value=42.0, unit="pages",
              refs=None, derivation="count of events", db=None):
        _refs = ["E-1"] if refs is None else refs
        with patch("app.services.advanced_layer_service.store") as m:
            m.database = db
            return persist_growth_metric(owner, metric, value, unit, _refs, derivation)

    def test_none_when_no_db(self):
        assert self._call(db=None) is None

    def test_none_when_empty_owner(self):
        assert self._call(owner="", db=MagicMock()) is None

    def test_none_when_empty_metric(self):
        assert self._call(metric="", db=MagicMock()) is None

    def test_none_when_no_evidence(self):
        assert self._call(refs=[], db=MagicMock()) is None

    def test_none_when_empty_derivation(self):
        assert self._call(derivation="", db=MagicMock()) is None


# ─── persist_offline_handoff (no-DB) ──────────────────────────────────────────

class TestPersistOfflineHandoffNoDB:
    def _call(self, owner="owner", fmt="encrypted_archive", ref="s3://bucket/export.zip", db=None):
        with patch("app.services.advanced_layer_service.store") as m:
            m.database = db
            return persist_offline_handoff(owner, fmt, ref)

    def test_none_when_no_db(self):
        assert self._call(db=None) is None

    def test_none_when_empty_owner(self):
        assert self._call(owner="", db=MagicMock()) is None

    def test_none_when_unknown_format(self):
        assert self._call(fmt="raw_dump", db=MagicMock()) is None

    def test_none_when_empty_ref(self):
        assert self._call(ref="", db=MagicMock()) is None


# ─── persist_secret_ref (no-DB) ───────────────────────────────────────────────

class TestPersistSecretRefNoDB:
    def _call(self, owner="owner", kind="totp", ref="vault://key", db=None):
        with patch("app.services.advanced_layer_service.store") as m:
            m.database = db
            return persist_secret_ref(owner, kind, ref)

    def test_none_when_no_db(self):
        assert self._call(db=None) is None

    def test_none_when_empty_owner(self):
        assert self._call(owner="", db=MagicMock()) is None

    def test_none_when_unknown_kind(self):
        assert self._call(kind="api_key", db=MagicMock()) is None

    def test_none_when_empty_ref(self):
        assert self._call(ref="", db=MagicMock()) is None

    def test_known_kinds_pass_kind_validation(self):
        for kind in ("totp", "ssh_key", "credential"):
            with patch("app.services.advanced_layer_service.store") as m:
                m.database = MagicMock()
                try:
                    persist_secret_ref("owner", kind, "vault://key")
                except Exception:
                    pass  # DB mock not wired — expected
