from __future__ import annotations

from pathlib import Path
from typing import Iterable

from docx import Document
from fpdf import FPDF

from app.core.config import settings
from app.services.file_utils import ensure_dir
from app.services.models import Chapter, DocumentBundle, KnowledgeDocument


def _timestamp_link(timestamp: float, source_url: str | None) -> str:
    if not source_url:
        return f"{timestamp:.0f}s"
    return f"[{timestamp:.0f}s]({source_url}?t={int(timestamp)})"


def render_markdown(doc: KnowledgeDocument) -> str:
    lines: list[str] = [f"# {doc.title}", "", "## Overview", doc.overview, ""]
    lines.append("## Table of Contents")
    for chapter in doc.chapters:
        lines.append(f"- [{chapter.title}](#{chapter.title.lower().replace(' ', '-')})")
    lines.append("")

    for chapter in doc.chapters:
        lines.append(f"## {chapter.title}")
        lines.append(f"Timestamp: {_timestamp_link(chapter.timestamp, chapter.source_url)}")
        lines.append("")
        lines.append(chapter.content)
        lines.append("")
        _append_section(lines, "Definitions", chapter.definitions)
        _append_section(lines, "Examples", chapter.examples)
        _append_section(lines, "Code Snippets", chapter.code_snippets)
        _append_section(lines, "Slide Text", chapter.slide_text)
        _append_section(lines, "Statistics", chapter.statistics)
        _append_section(lines, "Key Insights", chapter.insights)
        lines.append("")

    lines.append("## Key Insights")
    lines.extend([f"- {item}" for item in doc.key_takeaways])
    lines.append("")

    lines.append("## Knowledge Graph")
    lines.append("Nodes:")
    lines.extend([f"- {node['id']}" for node in doc.knowledge_graph.get("nodes", [])])
    lines.append("")

    lines.append("## Q&A")
    lines.extend([f"- {question}" for question in doc.questions])
    lines.append("")

    lines.append("## Flashcards")
    lines.extend([f"- {front} — {back}" for front, back in doc.flashcards])
    lines.append("")

    lines.append("## Summary")
    lines.append(doc.summary)
    lines.append("")

    lines.append("## Key Takeaways")
    lines.extend([f"- {takeaway}" for takeaway in doc.key_takeaways])
    lines.append("")

    lines.append("## Timeline Index")
    for entry in doc.timeline_index:
        lines.append(f"- {_timestamp_link(entry['timestamp'], entry.get('source_url'))}: {entry['title']}")
    lines.append("")

    return "\n".join(lines)


def _append_section(lines: list[str], title: str, items: Iterable[str]) -> None:
    items = list(items)
    if not items:
        return
    lines.append(f"### {title}")
    lines.extend([f"- {item}" for item in items])
    lines.append("")


def generate_documents(doc: KnowledgeDocument, job_id: str) -> DocumentBundle:
    ensure_dir(settings.documents_dir)
    markdown_path = settings.documents_dir / f"{job_id}.md"
    markdown_content = render_markdown(doc)
    markdown_path.write_text(markdown_content, encoding="utf-8")

    docx_path = _generate_docx(doc, job_id, markdown_content)
    pdf_path = _generate_pdf(doc, job_id, markdown_content)

    return DocumentBundle(markdown_path=markdown_path, pdf_path=pdf_path, docx_path=docx_path)


def _generate_docx(doc: KnowledgeDocument, job_id: str, markdown_content: str) -> Path | None:
    docx_path = settings.documents_dir / f"{job_id}.docx"
    document = Document()
    document.add_heading(doc.title, level=0)
    document.add_paragraph(doc.overview)
    document.add_paragraph("\n".join(markdown_content.splitlines()[4:]))
    document.save(docx_path)
    return docx_path


def _generate_pdf(doc: KnowledgeDocument, job_id: str, markdown_content: str) -> Path | None:
    pdf_path = settings.documents_dir / f"{job_id}.pdf"
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 10, doc.title)
    pdf.ln(2)
    for line in markdown_content.splitlines():
        pdf.multi_cell(0, 8, line)
    pdf.output(str(pdf_path))
    return pdf_path
