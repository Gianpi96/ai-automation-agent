import json
import logging
import time
import uuid
from app.services.groq_client import groq_client
from app.models.email_model import (
    Email, EmailCategory, EmailClassification, EmailDraft,
    EmailProcessResult, UrgencyLevel,
)

logger = logging.getLogger(__name__)

CLASSIFICATION_PROMPT = """You are an email classifier. Analyze the email and respond in JSON:
{
  "category": one of [support, billing, sales, complaint, inquiry, spam, other],
  "urgency": one of [low, medium, high, critical],
  "sentiment": brief description of tone (e.g. "frustrated", "polite", "neutral"),
  "key_topics": [list of main topics, max 5],
  "requires_response": true or false,
  "reasoning": "brief explanation of classification",
  "confidence": 0.0 to 1.0
}"""

DRAFT_PROMPT = """You are a professional email assistant. Write a response draft for this email.
The draft must be professional, empathetic, and helpful.
IMPORTANT: This is only a draft — it will NOT be sent without human review and approval.

Respond in JSON:
{
  "subject": "Re: [original subject]",
  "body": "full email body with proper greeting and signature placeholder",
  "tone": "professional/friendly/empathetic/formal"
}"""


async def classify_email(email: Email) -> EmailClassification:
    logger.info("Classifying email id=%s subject=%r", email.id, email.subject)
    messages = [
        {"role": "system", "content": CLASSIFICATION_PROMPT},
        {
            "role": "user",
            "content": f"From: {email.sender}\nSubject: {email.subject}\n\n{email.body}",
        },
    ]
    response = await groq_client.chat_json(messages=messages)
    raw = response.choices[0].message.content or "{}"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Classification JSON parse failed: %s", raw)
        data = {}

    return EmailClassification(
        email_id=email.id,
        category=_safe_enum(EmailCategory, data.get("category"), EmailCategory.OTHER),
        urgency=_safe_enum(UrgencyLevel, data.get("urgency"), UrgencyLevel.MEDIUM),
        sentiment=data.get("sentiment", "neutral"),
        key_topics=data.get("key_topics", []),
        requires_response=bool(data.get("requires_response", True)),
        reasoning=data.get("reasoning", ""),
        confidence=float(data.get("confidence", 0.7)),
    )


async def generate_draft(email: Email, classification: EmailClassification) -> EmailDraft:
    logger.info("Generating draft for email id=%s", email.id)
    messages = [
        {"role": "system", "content": DRAFT_PROMPT},
        {
            "role": "user",
            "content": (
                f"Original email:\nFrom: {email.sender}\nSubject: {email.subject}\n\n{email.body}\n\n"
                f"Classification: {classification.category} | Urgency: {classification.urgency} | "
                f"Sentiment: {classification.sentiment}"
            ),
        },
    ]
    response = await groq_client.chat_json(messages=messages)
    raw = response.choices[0].message.content or "{}"

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.error("Draft JSON parse failed: %s", raw)
        data = {"subject": f"Re: {email.subject}", "body": raw, "tone": "professional"}

    return EmailDraft(
        email_id=email.id,
        draft_id=str(uuid.uuid4()),
        subject=data.get("subject", f"Re: {email.subject}"),
        body=data.get("body", ""),
        tone=data.get("tone", "professional"),
        approved=False,
    )


async def process_email(email: Email) -> EmailProcessResult:
    start = time.monotonic()
    classification = await classify_email(email)
    draft = None
    if classification.requires_response and classification.category != EmailCategory.SPAM:
        draft = await generate_draft(email, classification)
    duration_ms = int((time.monotonic() - start) * 1000)
    return EmailProcessResult(
        email=email,
        classification=classification,
        draft=draft,
        processing_time_ms=duration_ms,
    )


def _safe_enum(enum_class, value, default):
    try:
        return enum_class(value)
    except (ValueError, KeyError):
        return default
