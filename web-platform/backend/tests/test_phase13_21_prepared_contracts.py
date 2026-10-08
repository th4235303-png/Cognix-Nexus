from __future__ import annotations

from datetime import datetime, timezone

from app.services.active_layer.execution import ExecutionLease, decide_execution
from app.services.learning_science.planning import LearningCandidate, build_path, priority
from app.services.life_integration.restore import authorize_restore
from app.services.life_integration.contracts import ContextRestoreRequest, PrivacyBoundary
from app.services.advanced_layer.vault import SecretRef, BreachCheckRequest, validate_secret_ref, validate_breach_prefix
from app.services.core_integration.document_assistant import DocumentClassification, OCRReview, classification_is_valid, lifecycle_transition_allowed
from app.services.core_integration.language_tutor import ParallelText, parallel_text_is_valid
from app.services.media_boundary.media_processing import MediaPackageManifest, package_is_valid
from app.services.media_boundary.metadata import MediaMetadata, metadata_is_safe
from app.services.media_boundary.native_capabilities import DeviceGate, capability_is_activatable
from app.services.release_evidence.operations import RecoveryDrill, recovery_is_evidenced
from app.services.release_evidence.checklist import ReleaseChecklist, checklist_status
from app.services.release_evidence.contracts import GateEvidence


def test_phase13_duplicate_and_terminal_execution_is_fail_closed():
    assert decide_execution("queued", "started", False).action == "start"
    assert decide_execution("running", "started", True).action == "ignore"
    assert decide_execution("completed", "retry_scheduled", False).action == "reject"
    assert ExecutionLease("r","o","l",1,"now","later").attempt == 1


def test_phase14_priority_is_deterministic():
    a = LearningCandidate("subject", 1.0, 0.0, 10.0, ("e1",))
    b = LearningCandidate("subject-2", 0.5, 0.0, 10.0, ("e2",))
    assert priority(a) > priority(b)
    assert build_path((b, a), 1)[0].subject_id == "subject"


def test_phase15_restore_requires_owner_and_explicit_request():
    request = ContextRestoreRequest("r", "owner", True, ("timeline",), "resume")
    boundary = PrivacyBoundary("user_content", "owner", "session")
    assert authorize_restore(request, boundary).allowed
    assert not authorize_restore(ContextRestoreRequest("r", "other", True, ("timeline",), "resume"), boundary).allowed


def test_phase16_secret_and_breach_boundaries():
    assert validate_secret_ref(SecretRef("s", "o", "totp", "cipher"))
    assert validate_breach_prefix(BreachCheckRequest("o", "abcde"))
    assert not validate_breach_prefix(BreachCheckRequest("o", "abcd"))


def test_phase17_document_and_tutor_contracts():
    assert classification_is_valid(DocumentClassification("invoice", 0.9))
    assert lifecycle_transition_allowed("processing", "review")
    assert not lifecycle_transition_allowed("processing", "indexed")
    review = OCRReview("doc", "text", ((0, 2),), "review")
    assert review.low_confidence_spans == ((0, 2),)
    assert parallel_text_is_valid(ParallelText("my", "ja", "မင်္ဂလာပါ", "こんにちは"))


def test_phase18_media_package_and_metadata():
    assert package_is_valid(MediaPackageManifest("owner", ("asset-1",)))
    assert metadata_is_safe(MediaMetadata(width=100, height=200))
    assert not metadata_is_safe(MediaMetadata(width=0))


def test_phase19_device_capability_requires_explicit_gate():
    assert capability_is_activatable(DeviceGate("camera", True, True))
    assert not capability_is_activatable(DeviceGate("camera", True, False))


def test_phase20_recovery_requires_observed_evidence():
    assert recovery_is_evidenced(RecoveryDrill("d", "backup_restore", True, True, "evidence://1"))
    assert not recovery_is_evidenced(RecoveryDrill("d", "rollback", True, True, None))


def test_phase21_release_checklist_requires_every_gate():
    checklist = ReleaseChecklist(
        "revision",
        ("ci", "browser"),
        (
            GateEvidence("ci", "pass", "e1", datetime.now(timezone.utc).isoformat()),
            GateEvidence("browser", "pass", "e2", datetime.now(timezone.utc).isoformat()),
        ),
    )
    assert checklist_status(checklist) == "pass"
    blocked = ReleaseChecklist("revision", ("ci",), (GateEvidence("ci", "pass", None),))
    assert checklist_status(blocked) == "fail"
