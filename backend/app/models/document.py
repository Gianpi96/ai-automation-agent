from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"


class ExtractionMethod(str, Enum):
    TEXT = "text"
    OCR = "ocr"


class DocumentChunk(BaseModel):
    index: int
    text: str
    token_count: int


class DocumentMetadata(BaseModel):
    filename: str
    file_hash: str
    file_size: int
    doc_type: DocumentType
    total_chars: int
    extraction_method: ExtractionMethod
    chunk_count: int
    cached: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentUploadResponse(BaseModel):
    document_id: str
    metadata: DocumentMetadata
    chunks: list[DocumentChunk]
    message: str


class DocumentQueryRequest(BaseModel):
    document_id: str
    question: str = Field(..., min_length=1, max_length=1000)


class DocumentQueryResponse(BaseModel):
    document_id: str
    question: str
    answer: str
    relevant_chunks: list[int]
    confidence: float = Field(ge=0.0, le=1.0)
