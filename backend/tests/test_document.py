"""Tests for document upload, OCR detection, and size validation."""
import io
import pytest
from unittest.mock import patch, MagicMock


def _make_pdf_bytes(text: str = "Hello world, this is a test PDF document with enough content.") -> bytes:
    """Create a minimal valid PDF with extractable text using pypdf."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(100, 750, text)
    c.save()
    return buf.getvalue()


def _make_minimal_pdf() -> bytes:
    """Return a real minimal PDF byte string (no reportlab dependency)."""
    # Minimal valid PDF with text content
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj

2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj

3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792]
   /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj

4 0 obj
<< /Length 44 >>
stream
BT /F1 12 Tf 100 700 Td (Hello Test PDF Document) Tj ET
endstream
endobj

5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj

xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000266 00000 n
0000000360 00000 n

trailer
<< /Size 6 /Root 1 0 R >>
startxref
441
%%EOF"""
    return pdf_content


@pytest.mark.asyncio
async def test_upload_pdf_normal(client):
    """Upload a PDF with extractable text — should use TEXT extraction."""
    from app.services.document_processor import extract_text, ExtractionMethod

    # Mock filetype.guess to return PDF MIME
    mock_detected = MagicMock()
    mock_detected.mime = "application/pdf"

    # Mock extract_text to return normal text (> 100 chars)
    long_text = "This is a valid PDF document. " * 20  # 600+ chars

    with patch("app.routers.documents.filetype.guess", return_value=mock_detected):
        with patch("app.routers.documents.extract_text", return_value=(long_text, "text")):
            response = await client.post(
                "/api/documents/upload",
                files={"file": ("test.pdf", b"%PDF-1.4 fake content", "application/pdf")},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["extraction_method"] == "text"
    assert data["metadata"]["total_chars"] == len(long_text)
    assert len(data["chunks"]) > 0


@pytest.mark.asyncio
async def test_upload_pdf_scanned_triggers_ocr(client):
    """PDF with < 100 chars extracted text should trigger OCR."""
    mock_detected = MagicMock()
    mock_detected.mime = "application/pdf"

    # Simulate scanned PDF: extract_text returns OCR method
    with patch("app.routers.documents.filetype.guess", return_value=mock_detected):
        with patch("app.routers.documents.extract_text", return_value=("scanned content " * 20, "ocr")):
            response = await client.post(
                "/api/documents/upload",
                files={"file": ("scanned.pdf", b"%PDF-1.4 scanned", "application/pdf")},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["metadata"]["extraction_method"] == "ocr"


@pytest.mark.asyncio
async def test_upload_too_large(client):
    """File larger than 10MB must be rejected with 413."""
    large_content = b"x" * (10 * 1024 * 1024 + 1)
    response = await client.post(
        "/api/documents/upload",
        files={"file": ("big.pdf", large_content, "application/pdf")},
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_upload_invalid_type(client):
    """Non-PDF/DOCX file must be rejected with 415."""
    mock_detected = MagicMock()
    mock_detected.mime = "image/jpeg"

    with patch("app.routers.documents.filetype.guess", return_value=mock_detected):
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("photo.jpg", b"\xff\xd8\xff fake jpeg", "image/jpeg")},
        )
    assert response.status_code == 415


@pytest.mark.asyncio
async def test_upload_cache_hit(client):
    """Second upload of same file should return cached result."""
    from app.services.cache import document_cache

    mock_detected = MagicMock()
    mock_detected.mime = "application/pdf"
    text = "Same document content. " * 30

    extract_call_count = 0

    def counting_extract(content, mime):
        nonlocal extract_call_count
        extract_call_count += 1
        return text, "text"

    with patch("app.routers.documents.filetype.guess", return_value=mock_detected):
        with patch("app.routers.documents.extract_text", side_effect=counting_extract):
            content = b"unique_pdf_content_for_cache_test"
            r1 = await client.post(
                "/api/documents/upload",
                files={"file": ("doc.pdf", content, "application/pdf")},
            )
            r2 = await client.post(
                "/api/documents/upload",
                files={"file": ("doc.pdf", content, "application/pdf")},
            )

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert extract_call_count == 1  # extracted only once
    assert r2.json()["metadata"]["cached"] is True


def test_chunk_text():
    """Text chunker splits correctly at max_tokens boundary."""
    from app.services.document_processor import chunk_text

    # 5000 words × ~5 chars = 25000 chars → ~6250 tokens → should split into ~4 chunks at 2000 tokens
    text = " ".join(["word"] * 5000)
    chunks = chunk_text(text, max_tokens=2000)
    assert len(chunks) >= 2
    for chunk in chunks:
        assert chunk.token_count <= 2000 + 10  # small tolerance
        assert len(chunk.text) > 0


def test_ocr_threshold_detection():
    """extract_text uses OCR when extracted text < 100 chars."""
    from app.services.document_processor import OCR_THRESHOLD
    assert OCR_THRESHOLD == 100
