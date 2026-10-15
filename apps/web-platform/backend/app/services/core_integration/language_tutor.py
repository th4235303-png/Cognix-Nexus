from __future__ import annotations

"""Phase 17 language-tutor domain contracts; providers remain external gates."""

from dataclasses import dataclass
from typing import Literal

Language = Literal["my","ja","ko"]

@dataclass(frozen=True)
class ParallelText:
    source_language: Language
    target_language: Language
    source: str
    translation: str
    reading: str | None = None

@dataclass(frozen=True)
class TutorCorrection:
    original: str
    corrected: str
    explanation: str
    level: str

@dataclass(frozen=True)
class TutorGoal:
    framework: Literal["CEFR","JLPT","TOPIK"]
    level: str

def parallel_text_is_valid(item: ParallelText) -> bool:
    return bool(item.source.strip() and item.translation.strip() and item.source_language != item.target_language)
