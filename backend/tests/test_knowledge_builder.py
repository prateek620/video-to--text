from __future__ import annotations

import unittest

from app.services.knowledge_builder import build_document
from app.services.models import Transcript, TranscriptSegment


class KnowledgeBuilderTests(unittest.TestCase):
    def test_build_document_uses_transcript_content_for_overview_summary_and_chapters(self) -> None:
        transcript = Transcript(
            segments=[
                TranscriptSegment(
                    start=0.0,
                    end=8.0,
                    text="Today we discuss height growth patterns in teenagers and the role of sleep.",
                ),
                TranscriptSegment(
                    start=8.0,
                    end=16.0,
                    text="The video explains nutrition choices and exercise habits that support healthy development.",
                ),
                TranscriptSegment(
                    start=16.0,
                    end=24.0,
                    text="It also compares myths versus evidence from pediatric studies.",
                ),
            ]
        )

        document = build_document("Everything You Need To Know About Your Height", transcript, None)

        self.assertIn("height growth patterns", document.overview.lower())
        self.assertIn("nutrition choices", document.summary.lower())
        self.assertTrue(document.chapters)
        self.assertIn("height growth patterns", document.chapters[0].content.lower())
        self.assertEqual(document.chapters[0].statistics, [])
        self.assertEqual(document.chapters[0].slide_text, [])


if __name__ == "__main__":
    unittest.main()
