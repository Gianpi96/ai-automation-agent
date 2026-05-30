import asyncio
import email
import imaplib
import logging
from email.header import decode_header
from datetime import datetime, UTC
import uuid
from app.config import settings
from app.models.email_model import Email

logger = logging.getLogger(__name__)


def _decode_header_value(raw: str | bytes | None) -> str:
    if not raw:
        return ""
    if isinstance(raw, bytes):
        raw = raw.decode(errors="replace")
    parts = decode_header(raw)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return " ".join(decoded)


def _get_body(msg: email.message.Message) -> str:
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in cd:
                try:
                    body = part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                    break
                except Exception:
                    continue
    else:
        try:
            body = msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", errors="replace"
            )
        except Exception:
            body = str(msg.get_payload())
    return body.strip()[:3000]  # limit body length


def _fetch_emails_sync(limit: int) -> list[Email]:
    if not settings.imap_host or not settings.imap_user:
        raise ValueError("IMAP non configurato. Imposta IMAP_HOST, IMAP_USER, IMAP_PASSWORD nel .env")

    imap_class = imaplib.IMAP4_SSL if settings.imap_use_ssl else imaplib.IMAP4
    conn = imap_class(settings.imap_host, settings.imap_port)
    conn.login(settings.imap_user, settings.imap_password)
    conn.select("INBOX")

    _, data = conn.search(None, "UNSEEN")
    ids = data[0].split()[-limit:]  # last N unread

    emails: list[Email] = []
    for eid in ids:
        _, msg_data = conn.fetch(eid, "(RFC822)")
        raw = msg_data[0][1]
        msg = email.message_from_bytes(raw)

        sender = _decode_header_value(msg.get("From", ""))
        subject = _decode_header_value(msg.get("Subject", "(nessun oggetto)"))
        body = _get_body(msg)
        date_str = msg.get("Date", "")

        emails.append(Email(
            id=f"imap_{eid.decode()}_{uuid.uuid4().hex[:6]}",
            sender=sender,
            subject=subject,
            body=body,
            received_at=datetime.now(UTC),
        ))

    conn.logout()
    return emails


async def fetch_real_emails(limit: int = 10) -> list[Email]:
    """Fetch unread emails from IMAP in a thread (imaplib is sync)."""
    return await asyncio.to_thread(_fetch_emails_sync, limit)
