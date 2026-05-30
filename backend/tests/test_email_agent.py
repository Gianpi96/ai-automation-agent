"""Tests for email classification and draft generation."""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.email_model import Email, EmailCategory, UrgencyLevel


def _mock_groq_json(data: dict):
    msg = MagicMock()
    msg.content = json.dumps(data)
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


COMPLAINT_EMAIL = Email(
    id="test_001",
    sender="angry@test.com",
    subject="This is terrible!",
    body="I am very unhappy with your service. My order is wrong and support ignored me.",
)

INQUIRY_EMAIL = Email(
    id="test_002",
    sender="curious@test.com",
    subject="Question about pricing",
    body="Hi, could you tell me about your pricing plans?",
)


@pytest.mark.asyncio
async def test_classify_complaint_email():
    """Complaint email should be classified as complaint with high urgency."""
    from app.agents.email_agent import classify_email

    mock_resp = _mock_groq_json({
        "category": "complaint",
        "urgency": "high",
        "sentiment": "frustrated",
        "key_topics": ["order issue", "support"],
        "requires_response": True,
        "reasoning": "Customer expressing anger about order",
        "confidence": 0.95,
    })

    with patch("app.agents.email_agent.groq_client") as mock_client:
        mock_client.chat_json = AsyncMock(return_value=mock_resp)
        result = await classify_email(COMPLAINT_EMAIL)

    assert result.category == EmailCategory.COMPLAINT
    assert result.urgency == UrgencyLevel.HIGH
    assert result.requires_response is True
    assert result.confidence > 0.5


@pytest.mark.asyncio
async def test_classify_inquiry_email():
    """Inquiry email should be classified correctly with medium urgency."""
    from app.agents.email_agent import classify_email

    mock_resp = _mock_groq_json({
        "category": "inquiry",
        "urgency": "medium",
        "sentiment": "neutral",
        "key_topics": ["pricing"],
        "requires_response": True,
        "reasoning": "Customer asking about pricing",
        "confidence": 0.9,
    })

    with patch("app.agents.email_agent.groq_client") as mock_client:
        mock_client.chat_json = AsyncMock(return_value=mock_resp)
        result = await classify_email(INQUIRY_EMAIL)

    assert result.category == EmailCategory.INQUIRY
    assert result.requires_response is True


@pytest.mark.asyncio
async def test_draft_not_auto_approved():
    """Drafts are NEVER auto-approved — they always start with approved=False."""
    from app.agents.email_agent import generate_draft, classify_email

    classify_resp = _mock_groq_json({
        "category": "complaint", "urgency": "high", "sentiment": "frustrated",
        "key_topics": ["order"], "requires_response": True,
        "reasoning": "complaint", "confidence": 0.9,
    })
    draft_resp = _mock_groq_json({
        "subject": "Re: This is terrible!",
        "body": "Dear Customer, I apologize for the inconvenience...",
        "tone": "empathetic",
    })

    with patch("app.agents.email_agent.groq_client") as mock_client:
        mock_client.chat_json = AsyncMock(side_effect=[classify_resp, draft_resp])
        classification = await classify_email(COMPLAINT_EMAIL)
        draft = await generate_draft(COMPLAINT_EMAIL, classification)

    assert draft.approved is False
    assert draft.approved_at is None
    assert len(draft.body) > 0


@pytest.mark.asyncio
async def test_spam_no_draft():
    """Spam emails should not get draft responses."""
    from app.agents.email_agent import process_email

    spam_email = Email(
        id="spam_001",
        sender="spam@spam.com",
        subject="You won $1M!!!",
        body="Click here to claim your prize!",
    )

    mock_resp = _mock_groq_json({
        "category": "spam",
        "urgency": "low",
        "sentiment": "suspicious",
        "key_topics": ["scam"],
        "requires_response": False,
        "reasoning": "Obvious spam",
        "confidence": 0.99,
    })

    with patch("app.agents.email_agent.groq_client") as mock_client:
        mock_client.chat_json = AsyncMock(return_value=mock_resp)
        result = await process_email(spam_email)

    assert result.draft is None
    assert result.classification.category == EmailCategory.SPAM


@pytest.mark.asyncio
async def test_approve_draft_api(client):
    """Test draft approval endpoint."""
    # First process an email to create a draft
    classify_resp = _mock_groq_json({
        "category": "inquiry", "urgency": "medium", "sentiment": "polite",
        "key_topics": ["pricing"], "requires_response": True,
        "reasoning": "inquiry", "confidence": 0.9,
    })
    draft_resp = _mock_groq_json({
        "subject": "Re: Question",
        "body": "Thank you for your question...",
        "tone": "professional",
    })

    with patch("app.agents.email_agent.groq_client") as mock_client:
        mock_client.chat_json = AsyncMock(side_effect=[classify_resp, draft_resp])
        result = await client.post("/api/emails/process/email_003")

    assert result.status_code == 200
    draft_id = result.json()["draft"]["draft_id"]

    # Approve the draft
    approval = await client.post(
        f"/api/emails/drafts/{draft_id}/approve",
        json={"approved": True},
    )
    assert approval.status_code == 200
    assert approval.json()["approved"] is True
    assert approval.json()["approved_at"] is not None


@pytest.mark.asyncio
async def test_process_all_emails(client):
    """Process all inbox emails returns list of results."""
    mock_resp = _mock_groq_json({
        "category": "inquiry", "urgency": "low", "sentiment": "neutral",
        "key_topics": ["general"], "requires_response": False,
        "reasoning": "test", "confidence": 0.8,
    })

    with patch("app.agents.email_agent.groq_client") as mock_client:
        mock_client.chat_json = AsyncMock(return_value=mock_resp)
        result = await client.post("/api/emails/process-all")

    assert result.status_code == 200
    data = result.json()
    assert isinstance(data, list)
    assert len(data) == 3  # 3 simulated emails
