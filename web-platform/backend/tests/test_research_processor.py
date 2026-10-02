import os
import unittest
from unittest.mock import patch

from app.services.research_processor import _wikipedia_rest_url, clean_text, mock_key_points, mock_summary, process_stage


class ResearchProcessorTests(unittest.TestCase):
    def test_clean_text_normalizes_whitespace(self):
        self.assertEqual(clean_text("  Hello   world\n\n  Second line "), "Hello world\nSecond line")

    def test_mock_summary_and_key_points_are_deterministic(self):
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."
        self.assertEqual(mock_summary(text), "First sentence. Second sentence! Third sentence?")
        self.assertEqual(mock_key_points(text), ["First sentence.", "Second sentence!", "Third sentence?", "Fourth sentence."])

    def test_wikipedia_urls_use_public_rest_fallback(self):
        self.assertEqual(
            _wikipedia_rest_url("https://en.wikipedia.org/wiki/Logistics"),
            "https://en.wikipedia.org/api/rest_v1/page/html/Logistics",
        )
        self.assertIsNone(_wikipedia_rest_url("https://example.com/wiki/Logistics"))

    def test_mock_processing_creates_translation_and_key_points(self):
        source = {"url": "https://example.com", "ai_summary": "A short summary."}
        with patch.dict(os.environ, {"COGNIX_PROCESSING_PROVIDER": "mock"}):
            translation = process_stage("translating", source)
            points = process_stage("key_points", source)
        self.assertEqual(translation.translation, "A short summary.")
        self.assertEqual(points.key_points, ["A short summary."])


if __name__ == "__main__":
    unittest.main()
