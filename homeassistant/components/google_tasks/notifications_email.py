"""Email notification handler for Google Tasks integration."""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib

from .exceptions import GoogleTaskNotificationError

_LOGGER = logging.getLogger(__name__)

SMTP_TIMEOUT = 30


async def async_send_email_notification(
    hass, config_entry, task_list: list[str]
) -> None:
    """Send a daily reminder email with the given task list."""

    if not task_list:
        _LOGGER.warning("Task list is empty, skipping email notification")
        return

    required_fields = ["smtp_username", "recipient_email", "smtp_password"]
    missing_fields = [
        field for field in required_fields if not config_entry.options.get(field)
    ]
    if missing_fields:
        raise GoogleTaskNotificationError(
            f"Missing required email configuration fields: {', '.join(missing_fields)}"
        )

    smtp_host = config_entry.options.get("smtp_host", "")
    print("SMTP Host is %s", smtp_host)
    try:
        smtp_port = int(config_entry.options.get("smtp_port", 587))
    except (ValueError, TypeError) as err:
        raise GoogleTaskNotificationError(
            f"Invalid port number: {config_entry.options.get('smtp_port')}"
        ) from err

    msg = MIMEMultipart()
    msg["From"] = config_entry.options.get("smtp_username")
    msg["To"] = config_entry.options.get("recipient_email")
    msg["Subject"] = "Daily reminder"

    task_count = len(task_list)
    body = (
        "Hi,\nGentle Reminder! \n\nThis is your To-do list for today:\n"
        f"You are pending with {task_count} task(s):\n\n"
        + "\n".join(f"- {task}" for task in task_list)
        + "\n\nBest Wishes, \nHome Assistant"
    )
    msg.attach(MIMEText(body, "plain"))

    server = None
    try:
        server = smtplib.SMTP(host_name, port, timeout=SMTP_TIMEOUT)
        server.starttls()
        server.login(config_entry.options.get("smtp_username"), config_entry.options.get("smtp_password"))
        server.sendmail(
            config_entry.options.get("smtp_username"),
            config_entry.options.get("recipient_email"),
            msg.as_string(),
        )
        _LOGGER.info(
            "Email notification sent successfully to %s with %d task(s)",
            config_entry.options.get("recipient_email"),
            task_count,
        )
    except smtplib.SMTPAuthenticationError as err:
        raise GoogleTaskNotificationError(
            "Authentication failed, check sender email and password"
        ) from err
    except smtplib.SMTPRecipientsRefused as err:
        raise GoogleTaskNotificationError(
            f"Recipient email address refused: {config_entry.options.get('recipient_email')}"
        ) from err
    except smtplib.SMTPSenderRefused as err:
        raise GoogleTaskNotificationError(
            f"Sender email address refused: {config_entry.options.get('smtp_username')}"
        ) from err
    except TimeoutError as err:
        raise GoogleTaskNotificationError(
            f"SMTP connection timed out after {SMTP_TIMEOUT} seconds"
        ) from err
    except (smtplib.SMTPException, OSError) as err:
        raise GoogleTaskNotificationError(
            f"Failed to send email notification: {err}"
        ) from err
    finally:
        if server is not None:
            try:
                server.quit()
            except smtplib.SMTPException:
                _LOGGER.debug("Error closing SMTP connection")
