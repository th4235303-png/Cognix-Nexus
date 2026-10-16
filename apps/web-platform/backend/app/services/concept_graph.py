"""Knowledge Concept Graph & Mindmap Generator.

Parses notes and document summaries into visual Mermaid graph and mindmap syntax
for visual understanding and dependency tracking.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class ConceptGraphService:
    """Extracts entity relations and builds interactive Mermaid diagrams."""

    @classmethod
    def generate_mermaid_mindmap(cls, topic: str, content: str) -> str:
        """Generate a valid Mermaid mindmap from text headers and bullet points."""
        clean_topic = re.sub(r'["\(\)\[\]]', "", topic).strip() or "Central Concept"
        lines = ["mindmap", f"  root(({clean_topic}))"]

        current_category = None
        for raw_line in content.split("\n"):
            line = raw_line.strip()
            if not line:
                continue

            # Header or bold title
            if line.startswith("#") or line.startswith("**"):
                clean_cat = re.sub(r'^[#*\s]+|[#*\s]+$', "", line)
                clean_cat = re.sub(r'["\(\)\[\]]', "", clean_cat)[:40]
                if clean_cat:
                    current_category = clean_cat
                    lines.append(f"    {clean_cat}")
            elif line.startswith("- ") or line.startswith("* "):
                bullet = line[2:].strip()
                clean_bullet = re.sub(r'["\(\)\[\]]', "", bullet)[:45]
                if clean_bullet:
                    indent = "      " if current_category else "    "
                    lines.append(f"{indent}{clean_bullet}")

        # If empty or minimal, construct structured fallback branches
        if len(lines) <= 2:
            lines.extend([
                "    Core Principles",
                "      Foundations",
                "      Mechanisms",
                "    Applications",
                "      Practical Use Cases",
                "      Implementation",
            ])

        return "\n".join(lines)

    @classmethod
    def generate_flowchart(cls, title: str, nodes: list[tuple[str, str, str]]) -> str:
        """Generate Mermaid flowchart TD from a list of (source, relation, target) tuples."""
        lines = ["flowchart TD"]
        for idx, (src, rel, tgt) in enumerate(nodes):
            src_id = f"N{idx}_A"
            tgt_id = f"N{idx}_B"
            lines.append(f'  {src_id}["{src}"] -->|"{rel}"| {tgt_id}["{tgt}"]')
        return "\n".join(lines)
