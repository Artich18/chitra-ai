"""Resume text extraction for PDF and DOCX uploads."""

from __future__ import annotations

import io


def extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    chunks: list[str] = []
    for page in reader.pages:
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(chunks).strip()


def extract_docx(data: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs if p.text).strip()


def extract_text(filename: str, content_type: str, data: bytes) -> tuple[str, str]:
    """Return (text, source). Source is 'pdf' | 'docx' | 'unknown'."""
    name = (filename or "").lower()
    ctype = (content_type or "").lower()
    if name.endswith(".pdf") or "pdf" in ctype:
        return extract_pdf(data), "pdf"
    if name.endswith(".docx") or "word" in ctype or "officedocument" in ctype:
        return extract_docx(data), "docx"
    # Fallback — try utf-8
    try:
        return data.decode("utf-8", errors="ignore"), "unknown"
    except Exception:
        return "", "unknown"
