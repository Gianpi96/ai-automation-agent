import logging
import asyncio
from datetime import datetime
from app.tools.registry import register_tool

logger = logging.getLogger(__name__)

_notifications_store: list[dict] = []

_SCHEMA = {
    "name": "send_notification",
    "description": "Send a notification message to the user or a specified channel. Stores the notification in the system.",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "The notification message to send",
            },
            "channel": {
                "type": "string",
                "description": "Notification channel: 'user', 'email', 'slack', 'system'",
                "enum": ["user", "email", "slack", "system"],
                "default": "user",
            },
            "priority": {
                "type": "string",
                "description": "Priority level: 'low', 'medium', 'high'",
                "enum": ["low", "medium", "high"],
                "default": "medium",
            },
        },
        "required": ["message"],
    },
}


@register_tool("send_notification", _SCHEMA)
async def send_notification(
    message: str,
    channel: str = "user",
    priority: str = "medium",
) -> str:
    logger.info("send_notification channel=%s priority=%s", channel, priority)
    await asyncio.sleep(0.05)

    notification = {
        "id": f"notif_{len(_notifications_store) + 1}",
        "message": message,
        "channel": channel,
        "priority": priority,
        "sent_at": datetime.utcnow().isoformat(),
        "delivered": True,
    }
    _notifications_store.append(notification)

    logger.info("Notification sent: %s", notification["id"])
    return f"Notification sent successfully via '{channel}' (priority: {priority}). ID: {notification['id']}"


def get_all_notifications() -> list[dict]:
    return list(_notifications_store)
