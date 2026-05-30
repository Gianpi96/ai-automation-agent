import logging
import time
import uuid
import filetype
from datetime import datetime, UTC
from fastapi import APIRouter, File, HTTPException, UploadFile
from app.config import settings
from app.services.stats import tracker, ExecutionRecord
from app.models.document import (
    DocumentMetadata, DocumentType, DocumentUploadResponse,
    DocumentQueryRequest, DocumentQueryResponse,
)
from app.services.cache import document_cache, file_hash
from app.services.document_processor import ALLOWED_MIME_TYPES, chunk_text, extract_text
from app.agents.document_agent import query_document

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentUploadResponse:
    content = await file.read()

    # Size validation
    if len(content) > settings.max_upload_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size is {settings.max_upload_size // 1024 // 1024}MB.",
        )

    # MIME type detection (use filetype library, not trust client header)
    detected = filetype.guess(content)
    if detected is None:
        raise HTTPException(status_code=415, detail="Cannot detect file type.")

    mime = detected.mime
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{mime}'. Only PDF and DOCX are allowed.",
        )

    # Check cache
    fhash = file_hash(content)
    cached = document_cache.get(fhash)
    if cached:
        logger.info("Cache HIT for document hash=%s", fhash[:8])
        cached["metadata"]["cached"] = True
        return DocumentUploadResponse(**cached)

    # Extract text
    try:
        text, extraction_method = extract_text(content, mime)
    except Exception as e:
        logger.error("Text extraction failed: %s", e)
        raise HTTPException(status_code=422, detail=f"Failed to extract text: {e}")

    # Chunk text
    chunks = chunk_text(text, max_tokens=2000)

    doc_type = DocumentType(ALLOWED_MIME_TYPES[mime])
    document_id = str(uuid.uuid4())
    metadata = DocumentMetadata(
        filename=file.filename or "unknown",
        file_hash=fhash,
        file_size=len(content),
        doc_type=doc_type,
        total_chars=len(text),
        extraction_method=extraction_method,
        chunk_count=len(chunks),
        cached=False,
    )

    response_data = {
        "document_id": document_id,
        "metadata": metadata.model_dump(),
        "chunks": [c.model_dump() for c in chunks],
        "message": f"Document processed with {extraction_method} extraction. {len(chunks)} chunks created.",
    }

    document_cache.set(fhash, response_data)
    tracker.record(ExecutionRecord(
        agent_id="document-agent",
        agent_name="Agente Documenti",
        status="completed",
        started_at=datetime.now(UTC),
        duration_ms=0,
        iterations=1,
        tools_used=[],
    ))
    logger.info("Document uploaded id=%s method=%s chunks=%d", document_id, extraction_method, len(chunks))
    return DocumentUploadResponse(**response_data)


@router.post("/query", response_model=DocumentQueryResponse)
async def query_doc(request: DocumentQueryRequest) -> DocumentQueryResponse:
    """Query a previously uploaded document."""
    # In production, retrieve from DB; here we use cache by document_id
    # For simplicity: client must pass document_id from upload response
    # Retrieve from cache (search all entries)
    found = None
    for key in list(document_cache._store.keys()):
        entry = document_cache.get(key)
        if entry and entry.get("document_id") == request.document_id:
            found = entry
            break

    if not found:
        raise HTTPException(status_code=404, detail="Document not found or cache expired. Please re-upload.")

    from app.models.document import DocumentChunk
    chunks = [DocumentChunk(**c) for c in found["chunks"]]

    try:
        result = await query_document(request.document_id, request.question, chunks)
        return result
    except Exception as e:
        logger.error("Document query failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
