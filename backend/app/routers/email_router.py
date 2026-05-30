import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.models.email_model import (
    Email, EmailProcessResult, DraftApprovalRequest, EmailDraft,
)
from app.agents.email_agent import process_email

router = APIRouter(prefix="/api/emails", tags=["emails"])
logger = logging.getLogger(__name__)

# In-memory store (replace with DB in production)
_email_results: dict[str, EmailProcessResult] = {}
_drafts: dict[str, EmailDraft] = {}

SIMULATED_EMAILS = [
    Email(
        id="email_001",
        sender="angry.customer@example.com",
        subject="URGENT: My order has been wrong for 3 weeks!",
        body=(
            "I placed order #12345 three weeks ago and it arrived completely wrong. "
            "I've called support twice already with no resolution. This is completely "
            "unacceptable. I want a full refund immediately or I will dispute the charge."
        ),
    ),
    Email(
        id="email_002",
        sender="enterprise@bigcorp.com",
        subject="Interested in enterprise pricing",
        body=(
            "Hello, we are a Fortune 500 company with 5000 employees and we're "
            "evaluating your solution. Could you provide enterprise pricing and "
            "a demo? Our budget is approved for Q1."
        ),
    ),
    Email(
        id="email_003",
        sender="user@example.com",
        subject="How do I reset my password?",
        body="Hi, I forgot my password and can't log in. How can I reset it? Thanks!",
    ),
]


@router.get("/inbox", response_model=list[Email])
async def get_inbox() -> list[Email]:
    """Get simulated inbox emails."""
    return SIMULATED_EMAILS


@router.post("/process/{email_id}", response_model=EmailProcessResult)
async def process_email_by_id(email_id: str) -> EmailProcessResult:
    """Classify an email and generate a draft response if needed."""
    email = next((e for e in SIMULATED_EMAILS if e.id == email_id), None)
    if not email:
        raise HTTPException(status_code=404, detail=f"Email {email_id} not found")

    try:
        result = await process_email(email)
        _email_results[email_id] = result
        if result.draft:
            _drafts[result.draft.draft_id] = result.draft
        return result
    except Exception as e:
        logger.error("Email processing failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/process-all", response_model=list[EmailProcessResult])
async def process_all_emails() -> list[EmailProcessResult]:
    """Process all emails in the simulated inbox."""
    results = []
    for email in SIMULATED_EMAILS:
        try:
            result = await process_email(email)
            _email_results[email.id] = result
            if result.draft:
                _drafts[result.draft.draft_id] = result.draft
            results.append(result)
        except Exception as e:
            logger.error("Failed to process email %s: %s", email.id, e)
    return results


@router.post("/drafts/{draft_id}/approve", response_model=EmailDraft)
async def approve_draft(draft_id: str, request: DraftApprovalRequest) -> EmailDraft:
    """
    Approve or reject a draft. IMPORTANT: drafts are NEVER auto-sent.
    Human approval is always required.
    """
    draft = _drafts.get(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail=f"Draft {draft_id} not found")

    if request.approved:
        draft.approved = True
        draft.approved_at = datetime.utcnow()
        if request.modifications:
            draft.body = request.modifications
        logger.info("Draft %s approved by user", draft_id)
    else:
        logger.info("Draft %s rejected by user", draft_id)

    return draft


@router.get("/drafts", response_model=list[EmailDraft])
async def list_drafts() -> list[EmailDraft]:
    return list(_drafts.values())
