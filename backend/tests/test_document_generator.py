from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.services.document_generator import generate_documents
from app.services.models import Chapter, KnowledgeDocument


class DocumentGeneratorTests(unittest.TestCase):
    def test_generate_documents_writes_multiline_pdf_without_crashing(self) -> None:
        chapter_content = "First line of content.\nSecond line of content."
        doc = KnowledgeDocument(
            title="Test title",
            overview="Overview",
            chapters=[
                Chapter(
                    title="Chapter 1",
                    timestamp=0.0,
                    content=chapter_content,
                    source_url="https://example.com",
                )
            ],
            key_takeaways=["Takeaway"],
            summary="Summary",
            knowledge_graph={"nodes": [{"id": "node-1"}]},
            flashcards=[("Front", "Back")],
            questions=["Question?"],
            timeline_index=[{"timestamp": 0.0, "title": "Chapter 1", "source_url": "https://example.com"}],
            source_urls=["https://example.com"],
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            documents_dir = Path(tmp_dir)
            with patch("app.services.document_generator.settings.documents_dir", documents_dir):
                bundle = generate_documents(doc, "test-job-multiline")
                self.assertIsNotNone(bundle.pdf_path)
                self.assertTrue(bundle.pdf_path.exists())
                self.assertGreater(bundle.pdf_path.stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
