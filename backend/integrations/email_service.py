"""Email notifications via SMTP (Gmail)."""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import settings
import logging

logger = logging.getLogger(__name__)


async def send_email(
    to: str,
    subject: str,
    body_html: str,
    body_text: str = "",
) -> bool:
    """Send an HTML email via SMTP."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_FROM
        msg["To"] = to

        if body_text:
            msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=True,
        )
        logger.info(f"Email sent to {to}: {subject}")
        return True
    except Exception as e:
        logger.error(f"Email failed to {to}: {e}")
        return False


async def send_task_reminder(to: str, task_title: str, due_date: str):
    subject = f"Task Reminder: {task_title}"
    html = f"""
    <div style="font-family:Inter,sans-serif;max-width:600px;margin:0 auto;">
      <h2 style="color:#3B82F6;">Task Reminder</h2>
      <p>Your task <strong>{task_title}</strong> is due on <strong>{due_date}</strong>.</p>
      <a href="{settings.FRONTEND_URL}/tasks"
         style="background:#3B82F6;color:white;padding:10px 20px;border-radius:6px;text-decoration:none;">
        View Task
      </a>
    </div>
    """
    return await send_email(to, subject, html)


async def send_weekly_report(to: str, report_html: str):
    subject = "Your Weekly MCP System Report"
    return await send_email(to, subject, report_html)
