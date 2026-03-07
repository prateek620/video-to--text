from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.models import (
    DocumentBundle,
    FrameDescription,
    FrameText,
    Transcript,
    TranscriptSegment,
    VideoKnowledge,
)
from app.services.pipeline import VideoProcessingPipeline


class PipelineKnowledgeBuildTests(unittest.TestCase):
    def test_build_knowledge_includes_audio_ocr_and_visual_content(self) -> None:
        knowledge_item = VideoKnowledge(
            source_id="video-1",
            source_url="https://example.com/video",
            transcript=Transcript(
                segments=[
                    TranscriptSegment(
                        start=0.0,
                        end=5.0,
                        text="The speaker explains the full photosynthesis process in simple terms.",
                    )
                ]
            ),
            ocr_text=[FrameText(timestamp=6.0, text="Chlorophyll absorbs sunlight to make glucose.")],
            visuals=[FrameDescription(timestamp=9.0, description="Animated diagram shows oxygen release from leaves.")],
            scenes=[],
            fusion_summary="",
        )

        pipeline = VideoProcessingPipeline()
        fake_bundle = DocumentBundle(markdown_path=Path("/tmp/fake.md"), pdf_path=None, docx_path=None)

        with patch("app.services.pipeline.generate_documents", return_value=fake_bundle) as generate_documents_mock:
            with patch("app.services.pipeline.KnowledgeIndex") as index_cls:
                result = pipeline.build_knowledge("job-1", "Detailed Notes", [knowledge_item])

        document = generate_documents_mock.call_args.args[0]
        full_content = " ".join(chapter.content for chapter in document.chapters).lower()
        self.assertIn("photosynthesis process", full_content)
        self.assertIn("visible on screen", full_content)
        self.assertIn("chlorophyll absorbs sunlight", full_content)
        self.assertIn("visual context", full_content)
        self.assertIn("oxygen release", full_content)
        self.assertEqual(result.document_bundle, fake_bundle)
        index_cls.return_value.build.assert_called_once()


if __name__ == "__main__":
    unittest.main()
