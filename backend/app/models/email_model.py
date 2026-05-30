from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from enum import Enum


class EmailCategory(str, Enum):
    SUPPORT = "support"
    BILLING = "billing"
    SALES = "sales"
    COMPLAINT = "complaint"
    INQUIRY = "inquiry"
    SPAM = "spam"
    OTHER = "other"


class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Email(BaseModel):
    id: str
    sender: str
    subject: str
    body: str
    received_at: datetime = Field(default_factory=datetime.utcnow)
    attachments: list[str] = []


class EmailClassification(BaseModel):
    email_id: str
    category: EmailCategory
    urgency: UrgencyLevel
    sentiment: str
    key_topics: list[str]
    requires_response: bool
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)


class EmailDraft(BaseModel):
    email_id: str
    draft_id: str
    subject: str
    body: str
    tone: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    approved: bool = False
    approved_at: datetime | None = None


class EmailProcessResult(BaseModel):
    email: Email
    classification: EmailClassification
    draft: EmailDraft | None = None
    processing_time_ms: int = 0


class DraftApprovalRequest(BaseModel):
    approved: bool
    modifications: str | None = None
