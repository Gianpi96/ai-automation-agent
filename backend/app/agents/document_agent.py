import json
import logging
from app.services.groq_client import groq_client
from app.models.document import DocumentChunk, DocumentQueryResponse

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a document analysis assistant. You are given chunks of text from a document and must answer questions accurately based solely on the provided content.

Respond in JSON with this exact structure:
{
  "answer": "detailed answer based on the document",
  "relevant_chunks": [list of chunk indices used, e.g. [0, 2]],
  "confidence": 0.0 to 1.0
}

If the answer is not found in the document, set confidence below 0.5 and state that clearly."""


async def query_document(
    document_id: str,
    question: str,
    chunks: list[DocumentChunk],
) -> DocumentQueryResponse:
    logger.info("Document query doc_id=%s question=%r chunks=%d", document_id, question, len(chunks))

    context = "\n\n".join(
        f"[Chunk {c.index}]\n{c.text}" for c in chunks
    )

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"Document content:\n\n{context}\n\nQuestion: {question}",
        },
    ]

    response = await groq_client.chat_json(messages=messages)
    raw = response.choices[0].message.content or "{}"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON from Groq: %s", raw)
        data = {"answer": raw, "relevant_chunks": [], "confidence": 0.5}

    return DocumentQueryResponse(
        document_id=document_id,
        question=question,
        answer=data.get("answer", "Unable to answer"),
        relevant_chunks=data.get("relevant_chunks", []),
        confidence=float(data.get("confidence", 0.5)),
    )
