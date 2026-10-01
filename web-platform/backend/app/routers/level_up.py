from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.services.level_up import (
    analyze_gap, build_learning_path, compounding_score, decay_review, decision_balance,
    detect_sync_conflict, feynman_grade, interleave, legacy_policy, research_mode,
    restore_context, synthesis_contract, wiki_projection, writing_citation_check,
)
from app.store import store

router = APIRouter(prefix="/brain/level-up", tags=["level-up"])

class FeynmanIn(BaseModel):
    topic: str = Field(min_length=1, max_length=300)
    explanation: str = Field(min_length=1, max_length=12000)
    required_terms: list[str] = Field(default_factory=list, max_length=100)

@router.post("/feynman")
def feynman(payload: FeynmanIn):
    return {"topic": payload.topic, **feynman_grade(payload.explanation, payload.required_terms)}

class DecayIn(BaseModel):
    stability: float = Field(gt=0, le=10000)
    difficulty: float = Field(ge=1, le=10)
    last_reviewed: datetime

@router.post("/decay")
def decay(payload: DecayIn):
    return decay_review(payload.stability, payload.difficulty, payload.last_reviewed)

class InterleaveIn(BaseModel):
    subjects: list[str] = Field(min_length=2, max_length=20)
    rounds: int = Field(default=3, ge=1, le=20)

@router.post("/interleave")
def interleave_route(payload: InterleaveIn):
    try:
        return {"sequence": interleave(payload.subjects, payload.rounds)}
    except ValueError as exc:
        raise HTTPException(400, str(exc))

class PathIn(BaseModel):
    goal: str = Field(min_length=1, max_length=2000)
    items: list[dict] = Field(default_factory=list, max_length=100)

@router.post("/learning-path")
def path(payload: PathIn):
    return build_learning_path(payload.items, payload.goal)

class GapIn(BaseModel):
    subject: str = Field(min_length=1, max_length=300)
    known: list[str] = Field(default_factory=list, max_length=200)
    required: list[str] = Field(default_factory=list, max_length=200)

@router.post("/knowledge-gap")
def gap(payload: GapIn):
    return analyze_gap(payload.subject, payload.known, payload.required)

class SynthesisIn(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    source_ids: list[str] = Field(min_length=3, max_length=50)
    findings: list[dict] = Field(default_factory=list, max_length=200)

@router.post("/synthesis")
def synthesis(payload: SynthesisIn):
    try:
        return synthesis_contract(payload.question, payload.source_ids, payload.findings)
    except ValueError as exc:
        raise HTTPException(400, str(exc))

class DecisionIn(BaseModel):
    options: list[dict] = Field(min_length=2, max_length=20)
    evidence: list[dict] = Field(default_factory=list, max_length=200)

@router.post("/decision-support")
def decision(payload: DecisionIn):
    return decision_balance(payload.options, payload.evidence)

class WritingIn(BaseModel):
    source_ids: list[str] = Field(min_length=1, max_length=100)
    cited_ids: list[str] = Field(default_factory=list, max_length=100)

@router.post("/writing/citations")
def writing(payload: WritingIn):
    return writing_citation_check(payload.source_ids, payload.cited_ids)

class ResearchIn(BaseModel):
    source_ids: list[str] = Field(min_length=1, max_length=100)
    claims: list[dict] = Field(default_factory=list, max_length=200)

@router.post("/research")
def research(payload: ResearchIn):
    return research_mode(payload.source_ids, payload.claims)

class TimelineIn(BaseModel):
    events: list[dict] = Field(default_factory=list, max_length=500)

@router.post("/timeline/restore")
def timeline(payload: TimelineIn):
    return restore_context(payload.events)

@router.get("/mood-policy")
def mood():
    return {"storage":"local_only","server_logging":False,"cloud_sync":"disabled_by_default","inference":"user_triggered_only"}

@router.get("/ambient-policy")
def ambient():
    return {"mode":"user_triggered","background_listening":False,"continuous_location_tracking":False}

class ContextIn(BaseModel):
    events: list[dict] = Field(default_factory=list, max_length=200)

@router.post("/context/restore")
def context(payload: ContextIn):
    return restore_context(payload.events)

@router.get("/legacy/policy")
def legacy():
    return legacy_policy()

class WikiIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    body: str = Field(default="")
    source_ids: list[str] = Field(default_factory=list, max_length=100)

@router.post("/wiki/preview")
def wiki(payload: WikiIn):
    return wiki_projection(payload.title, payload.body, payload.source_ids)

class GrowthIn(BaseModel):
    concepts: int = Field(ge=0, le=1000000)
    notes: int = Field(ge=0, le=1000000)
    links: int = Field(ge=0, le=1000000)
    sources: int = Field(ge=0, le=1000000)

@router.post("/compounding")
def compounding(payload: GrowthIn):
    return {"score": compounding_score(payload.concepts, payload.notes, payload.links, payload.sources)}

class SyncIn(BaseModel):
    base_revision: int = Field(ge=0)
    local_revision: int = Field(ge=0)
    remote_revision: int = Field(ge=0)
    local: dict = Field(default_factory=dict)
    remote: dict = Field(default_factory=dict)

@router.post("/offline/sync-check")
def sync_check(payload: SyncIn):
    return detect_sync_conflict(payload.base_revision, payload.local_revision, payload.remote_revision, payload.local, payload.remote)

@router.get("/feature-matrix")
def feature_matrix():
    return {"features":[
      {"id":"4.1","name":"Agent Mode","status":"worker+evidence+review"},
      {"id":"4.2","name":"Synthesis Engine","status":"source-bound"},
      {"id":"4.3","name":"Decision Support","status":"balanced-evidence"},
      {"id":"4.4","name":"Writing Assistant","status":"citation-guarded"},
      {"id":"4.5","name":"Feynman Mode","status":"mastery-threshold"},
      {"id":"4.6","name":"Knowledge Decay","status":"retention-risk"},
      {"id":"4.7","name":"Interleaving","status":"2+ subjects"},
      {"id":"4.8","name":"Learning Path","status":"library-only"},
      {"id":"4.9","name":"Knowledge Gap","status":"explicit-gaps"},
      {"id":"4.10","name":"Research Mode","status":"source-bound+review"},
      {"id":"4.11","name":"Personal Timeline","status":"opt-in"},
      {"id":"4.12","name":"Mood-Aware","status":"local-only"},
      {"id":"4.13","name":"Ambient Learning","status":"user-triggered"},
      {"id":"4.14","name":"Context Restoration","status":"local-input"},
      {"id":"4.15","name":"Time Capsule","status":"encrypted"},
      {"id":"4.16","name":"Personal Wiki","status":"private"},
      {"id":"4.17","name":"Knowledge Compounding","status":"metric"},
      {"id":"4.18","name":"Idea Generator","status":"evidence-only boundary"},
      {"id":"4.19","name":"Offline-first AI","status":"encrypted-cache+explicit-cloud"},
      {"id":"4.20","name":"Legacy Mode","status":"encrypted+beneficiary"},
    ]}
