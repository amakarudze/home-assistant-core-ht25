"""Email notification handler for Google Tasks integration."""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib
<<<<<<< HEAD
import socket
=======
>>>>>>> 558a5dd53ce (merge payel-contrib branch without testing)

from .exceptions import GoogleTaskNotificationError

_LOGGER = logging.getLogger(__name__)

SMTP_TIMEOUT = 30  # SMTP timeout in seconds


def send_email_notification(task_list: list[str], email_config: dict[str, str]) -> None:
    """Send a daily reminder email with the given task list.

    Args:
        task_list: List of task titles to include in the email
        email_config: Dictionary containing email configuration with keys:
            - sender_email: Email address to send from
            - recipient_email: Email address to send to
            - sender_password: Password for sender email
            - host_name: SMTP server hostname (optional, defaults to smtp.gmail.com)
            - port: SMTP server port (optional, defaults to 587)

    Raises:
        GoogleTaskNotificationError: If email sending fails
    """
    # Validate input parameters
    if not task_list:
        _LOGGER.warning("Task list is empty, skipping email notification")
        return

    if not email_config:
        raise GoogleTaskNotificationError("Email configuration is missing")

    # Validate required email config fields
    required_fields = ["sender_email", "recipient_email", "sender_password"]
    missing_fields = [field for field in required_fields if not email_config.get(field)]
    if missing_fields:
        raise GoogleTaskNotificationError(
            f"Missing required email configuration fields: {', '.join(missing_fields)}"
        )

    # Get SMTP settings with defaults
    host_name = email_config.get("host_name", "smtp.gmail.com")
    try:
        port = int(email_config.get("port", 587))
    except (ValueError, TypeError) as err:
        raise GoogleTaskNotificationError(
            f"Invalid port number: {email_config.get('port')}"
        ) from err

    # Create the email content
    msg = MIMEMultipart()
    msg["From"] = email_config["sender_email"]
    msg["To"] = email_config["recipient_email"]
    msg["Subject"] = "Daily reminder"

    task_count = len(task_list)
    body_lines = [
        f"Here are your {task_count} Google Tasks to-do item(s) for today:",
        "",
    ]
    body_lines.extend(f"- {task}" for task in task_list)
    body = "\n".join(body_lines)
    msg.attach(MIMEText(body, "plain"))

    # Send email with error handling
    server = None
    try:
        server = smtplib.SMTP(host_name, port, timeout=SMTP_TIMEOUT)
        server.starttls()
        server.login(email_config["sender_email"], email_config["sender_password"])
        server.sendmail(
            email_config["sender_email"],
            email_config["recipient_email"],
            msg.as_string(),
        )
        _LOGGER.info(
            "Email notification sent successfully to %s with %d task(s)",
            email_config["recipient_email"],
            task_count,
        )
    except smtplib.SMTPAuthenticationError as err:
        raise GoogleTaskNotificationError(
            "Authentication failed, check sender email and password"
        ) from err
    except smtplib.SMTPRecipientsRefused as err:
        raise GoogleTaskNotificationError(
            f"Recipient email address refused: {email_config['recipient_email']}"
        ) from err
    except smtplib.SMTPSenderRefused as err:
        raise GoogleTaskNotificationError(
            f"Sender email address refused: {email_config['sender_email']}"
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
