from __future__ import annotations

import unittest

from app.services.knowledge_builder import build_document
from app.services.models import Transcript, TranscriptSegment


class KnowledgeBuilderTests(unittest.TestCase):
    def test_build_document_is_not_placeholder_driven(self) -> None:
        transcript = Transcript(
            segments=[
                TranscriptSegment(
                    start=0.0,
                    end=30.0,
                    text="Python decorators allow behavior extension without modifying original functions.",
                ),
                TranscriptSegment(
                    start=30.0,
                    end=60.0,
                    text="Example: logging decorators can wrap API handlers for request tracing.",
                ),
                TranscriptSegment(
                    start=60.0,
                    end=90.0,
                    text="This pattern improves maintainability and keeps business logic clean.",
                ),
            ]
        )

        doc = build_document("Decorator Deep Dive", transcript, "https://example.com/video")
        self.assertTrue(doc.chapters)

        all_content = " ".join(ch.content for ch in doc.chapters).lower()
        self.assertIn("decorators", all_content)
        self.assertNotIn("introduction to the topic and key objectives", all_content)

        self.assertTrue(doc.overview)
        self.assertTrue(doc.summary)
        self.assertTrue(doc.timeline_index)


if __name__ == "__main__":
    unittest.main()