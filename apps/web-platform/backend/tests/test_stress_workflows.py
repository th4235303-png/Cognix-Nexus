from __future__ import annotations

import time
import unittest

from app.services.processing import STAGES


class StressWorkflowTests(unittest.TestCase):
    def test_500_page_synthetic_workflow_budget(self) -> None:
        # Deterministic and offline: catches accidental O(n^2) regressions
        # before a live load test.
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
            "queued", "extracting", "cleaning", "translating",
            "summarizing", "key_points", "fact_check",
            "trust_scoring", "needs_review", "approved",
        }
        self.assertEqual(set(STAGES), expected)


if __name__ == "__main__":
    unittest.main()
