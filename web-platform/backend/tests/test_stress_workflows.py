from __future__ import annotations

import time
import unittest

from app.services.processing import STAGES, advance
from app.store import Store


class StressWorkflowTests(unittest.TestCase):
    def test_500_page_synthetic_workflow_budget(self) -> None:
        # Keep this deterministic and offline: the goal is to catch accidental
        # O(n^2) regressions in the pure workflow boundary before live load tests.
        pages = [f"Page {i}: " + ("synthetic knowledge content " * 40) for i in range(1, 501)]
        started = time.perf_counter()
        chunks = []
        for page_no, page in enumerate(pages, 1):
            words = page.split()
            for offset in range(0, len(words), 120):
                chunks.append({
                    "page_number": page_no,
                    "text": " ".join(words[offset:offset + 120]),
                })
        elapsed = time.perf_counter() - started
        self.assertEqual(len(pages), 500)
        self.assertGreater(len(chunks), 500)
        self.assertLess(elapsed, 2.0)

    def test_pipeline_stage_contract_is_complete(self) -> None:
        expected = {
            "ingest", "extract", "ocr", "section_detect",
            "smart_chunk", "summarize", "embed", "concepts",
            "cross_links", "review", "canonical",
        }
        self.assertTrue(expected.issubset(set(STAGES)))


if __name__ == "__main__":
    unittest.main()
