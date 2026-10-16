"""Spaced Repetition & Daily Quiz Engine.

Implements the SuperMemo SM-2 active recall algorithm and auto-generates
concept flashcard quizzes from notes without recurring cloud costs.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger(__name__)


class SpacedRepetitionQuizService:
    """Spaced Repetition SM-2 computation and Quiz generator."""

    @classmethod
    def calculate_sm2(
        cls,
        repetition: int,
        interval_days: int,
        ease_factor: float,
        quality: int,  # 0 to 5 (0-2 = fail, 3 = hard, 4 = good, 5 = easy)
    ) -> dict[str, Any]:
        """Compute next review interval and ease factor according to SM-2 formula.

        Args:
            repetition: Current consecutive correct recall count
            interval_days: Current review interval in days
            ease_factor: Current difficulty multiplier (min 1.3, default 2.5)
            quality: User recall rating (0 to 5)

        Returns:
            dict containing next_interval_days, new_repetition, new_ease_factor, next_review_at
        """
        # Constrain quality between 0 and 5
        q = max(0, min(5, quality))

        # Update ease factor: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = ease_factor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        new_ef = max(1.3, round(new_ef, 3))

        if q < 3:
            # Failed recall: reset repetition count, repeat tomorrow
            new_rep = 0
            new_interval = 1
        else:
            # Successful recall
            new_rep = repetition + 1
            if new_rep == 1:
                new_interval = 1
            elif new_rep == 2:
                new_interval = 6
            else:
                new_interval = round(interval_days * new_ef)

        next_date = datetime.now(timezone.utc) + timedelta(days=new_interval)

        return {
            "repetition": new_rep,
            "interval_days": new_interval,
            "ease_factor": new_ef,
            "next_review_at": next_date.isoformat(),
        }

    @classmethod
    def generate_quiz_from_notes(
        cls,
        title: str,
        content: str,
        max_cards: int = 5,
    ) -> list[dict[str, Any]]:
        """Extract concept pairs, definitions, or questions from note text."""
        cards = []
        sentences = [s.strip() for s in re.split(r"[.\n]+", content) if len(s.strip()) > 15]

        # 1. Look for definition patterns ("X is Y", "X means Y", "X refers to Y", "X: Y")
        def_pattern = re.compile(
            r"^([A-Z][A-Za-z0-9\s\-]{2,30})\s+(?:is|refers to|means|represents|defined as)\s+(.+)$",
            re.IGNORECASE,
        )

        for s in sentences:
            m = def_pattern.match(s)
            if m:
                term, explanation = m.groups()
                cards.append({
                    "card_id": f"card_{len(cards)+1}",
                    "question": f"What is {term.strip()}?",
                    "answer": explanation.strip(),
                    "source_context": s,
                    "repetition": 0,
                    "interval_days": 1,
                    "ease_factor": 2.5,
                })
                if len(cards) >= max_cards:
                    break

        # 2. Fallback heuristic: cloze deletion or key sentence question
        if not cards:
            for idx, s in enumerate(sentences[:max_cards]):
                words = s.split()
                if len(words) > 5:
                    key_word = max(words, key=len)
                    cloze = s.replace(key_word, "____", 1)
                    cards.append({
                        "card_id": f"card_{idx+1}",
                        "question": f"Fill in the blank: \"{cloze}\"",
                        "answer": key_word,
                        "source_context": s,
                        "repetition": 0,
                        "interval_days": 1,
                        "ease_factor": 2.5,
                    })

        return cards

    @classmethod
    def format_telegram_quiz(cls, card: dict[str, Any]) -> dict[str, Any]:
        """Format an interactive Telegram quiz prompt with SM-2 answer buttons."""
        card_id = card.get("card_id", "1")
        question = card.get("question", "")

        text = (
            f"🧠 <b>[Cognix Daily Flashcard]</b>\n\n"
            f"❓ <b>Question:</b>\n{question}\n\n"
            f"<i>Tap below to reveal answer and update your spaced repetition interval.</i>"
        )

        buttons = [
            [
                {"text": "💡 Reveal Answer", "callback_data": f"cognix_reveal:{card_id}"},
            ],
            [
                {"text": "🔴 Hard (1d)", "callback_data": f"cognix_grade_hard:{card_id}"},
                {"text": "🟢 Easy (+4d)", "callback_data": f"cognix_grade_easy:{card_id}"},
            ],
        ]

        return {"text": text, "inline_keyboard": buttons}
