from __future__ import annotations

from io import BytesIO
from pathlib import Path


def extract_text_from_upload(filename: str, content: bytes) -> str:
    extension = Path(filename).suffix.lower()

    if extension in {".txt", ".md", ".csv"}:
        return decode_text(content)
    if extension == ".pdf":
        return extract_pdf_text(content)
    if extension in {".docx", ".doc"}:
        return extract_docx_text(content)

    return decode_text(content)


def decode_text(content: bytes) -> str:
    for encoding in ("utf-8", "utf-16", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="ignore")


def extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception:
        return decode_text(content)


def extract_docx_text(content: bytes) -> str:
    try:
        from docx import Document

        document = Document(BytesIO(content))
        return "\n".join(paragraph.text for paragraph in document.paragraphs).strip()
    except Exception:
        return decode_text(content)

