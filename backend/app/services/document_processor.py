import io
import logging
from pathlib import Path
from app.models.document import DocumentChunk, ExtractionMethod

logger = logging.getLogger(__name__)

ALLOWED_MIME_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
}
OCR_THRESHOLD = 100  # chars; below this assume scanned PDF


def _virus_scan_placeholder(content: bytes) -> None:
    """Placeholder: real implementation would call ClamAV or similar."""
    logger.warning(
        "Virus scan not configured — skipping. Install ClamAV and configure for production."
    )


def _extract_pdf(content: bytes) -> tuple[str, ExtractionMethod]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    text = "\n".join(
        page.extract_text() or "" for page in reader.pages
    ).strip()

    if len(text) >= OCR_THRESHOLD:
        return text, ExtractionMethod.TEXT

    # Scanned PDF — fall back to OCR
    logger.info("PDF text < %d chars (%d), falling back to OCR", OCR_THRESHOLD, len(text))
    try:
        import pytesseract
        from PIL import Image
        from pypdf import PdfReader as _PdfReader
        import fitz  # PyMuPDF

        doc = fitz.open(stream=content, filetype="pdf")
        ocr_parts: list[str] = []
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_parts.append(pytesseract.image_to_string(img))
        return "\n".join(ocr_parts).strip(), ExtractionMethod.OCR
    except ImportError as e:
        logger.error("OCR dependencies missing (%s) — returning partial text", e)
        return text, ExtractionMethod.TEXT


def _extract_docx(content: bytes) -> tuple[str, ExtractionMethod]:
    from docx import Document

    doc = Document(io.BytesIO(content))
    text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return text, ExtractionMethod.TEXT


def extract_text(content: bytes, mime_type: str) -> tuple[str, ExtractionMethod]:
    _virus_scan_placeholder(content)
    doc_type = ALLOWED_MIME_TYPES.get(mime_type)
    if doc_type == "pdf":
        return _extract_pdf(content)
    if doc_type == "docx":
        return _extract_docx(content)
    raise ValueError(f"Unsupported MIME type: {mime_type}")


def chunk_text(text: str, max_tokens: int = 2000) -> list[DocumentChunk]:
    """Split text into chunks of roughly max_tokens (approx 4 chars/token)."""
    max_chars = max_tokens * 4
    words = text.split()
    chunks: list[DocumentChunk] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        word_len = len(word) + 1
        if current_len + word_len > max_chars and current:
            chunk_text = " ".join(current)
            chunks.append(DocumentChunk(
                index=len(chunks),
                text=chunk_text,
                token_count=len(chunk_text) // 4,
            ))
            current = [word]
            current_len = word_len
        else:
            current.append(word)
            current_len += word_len

    if current:
        chunk_text = " ".join(current)
        chunks.append(DocumentChunk(
            index=len(chunks),
            text=chunk_text,
            token_count=len(chunk_text) // 4,
        ))

    return chunks
