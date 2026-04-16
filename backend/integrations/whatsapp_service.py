"""WhatsApp automation via Twilio API."""
from twilio.rest import Client
from core.config import settings
import logging

logger = logging.getLogger(__name__)


def get_twilio_client() -> Client:
    return Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


async def send_whatsapp_message(to: str, message: str) -> dict:
    """
    Send a WhatsApp message via Twilio.
    `to` should be in format: +919876543210
    """
    try:
        client = get_twilio_client()
        to_whatsapp = f"whatsapp:{to}" if not to.startswith("whatsapp:") else to
        msg = client.messages.create(
            from_=settings.TWILIO_WHATSAPP_FROM,
            to=to_whatsapp,
            body=message,
        )
        logger.info(f"WhatsApp sent to {to}: SID={msg.sid}")
        return {"success": True, "sid": msg.sid, "status": msg.status}
    except Exception as e:
        logger.error(f"WhatsApp failed to {to}: {e}")
        return {"success": False, "error": str(e)}


async def send_task_alert_whatsapp(to: str, task_title: str, due_date: str) -> dict:
    message = (
        f"*MCP Task Alert*\n"
        f"Task: {task_title}\n"
        f"Due: {due_date}\n"
        f"Open dashboard: {settings.FRONTEND_URL}/tasks"
    )
    return await send_whatsapp_message(to, message)


async def send_lead_followup_whatsapp(to: str, name: str, message: str) -> dict:
    full_msg = f"Hi {name},\n\n{message}\n\n— Sent via MCP CRM"
    return await send_whatsapp_message(to, full_msg)
