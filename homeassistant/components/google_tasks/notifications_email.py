"""Email notification handler for Google Tasks integration."""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib
import socket

from .exceptions import GoogleTaskNotificationError

_LOGGER = logging.getLogger(__name__)

SMTP_TIMEOUT = 10  # SMTP timeout in seconds


def send_email_notification(task_list, email_config):
    """Send a daily reminder email with the given tasklist.

    Args:
        task_list (list): List of tasks to include in the email.
        email_config:Dictionary containing email configuration with keys:
        -sender_email: Email address to send from
        -recipient_email: Email address to send to
        -sender_password: Password for the sender email account

    Raises:
        GoogleTaskNotificationError: If email sending fails.
    """

    # Validate input parameters
    if not task_list:
        _LOGGER.warning("Task list is empty. No email sent")
        return

    if not email_config:
        raise GoogleTaskNotificationError("Email configuration is missing.")
    # Validate required email config fields
    required_fields = [
        "sender_email",
        "recipient_email",
        "sender_password",
    ]  # Use constants instead when definition is done
    missing_fields = [field for field in required_fields if not email_config.get(field)]
    if missing_fields:
        raise GoogleTaskNotificationError(
            f"Missing required email configuration fields: {', '.join(missing_fields)}"
        )

    # Create the email content
    task_count = len(task_list)
    msg = MIMEMultipart()
    msg["From"] = email_config["sender_email"]
    msg["To"] = email_config["recipient_email"]
    msg["Subject"] = "Task Reminder from Home Assistant"
    body = (
        "Hi,\nGentle Reminder! \n\nThis is your To-do list for today:\n"
        + "\n".join(f"- {task}" for task in task_list)
        + "\n\nBest Wishes, \nHome Assistant"
    )
    msg.attach(MIMEText(body, "plain"))

    # Send email with error handling
    server = None
    try:
        server = smtplib.SMTP(email_config["host_name"], email_config["port"])
        server.starttls()
        server.login(email_config["sender_email"], email_config["sender_password"])
        server.sendmail(
            email_config["sender_email"],
            email_config["recipient_email"],
            msg.as_string(),
        )
        _LOGGER.info("Email sent successfully!")
    except smtplib.SMTPAuthenticationError as err:
        raise GoogleTaskNotificationError(
            "Authentication failed. Check sender email and password."
        ) from err
    except smtplib.SMTPRecipientsRefused as err:
        raise GoogleTaskNotificationError(
            f"Recipient address refused: {email_config['recipient_email']}"
        ) from err
    except smtplib.SMTPSenderRefused as err:
        raise GoogleTaskNotificationError(
            f"Sender email address refused: {email_config['sender_email']}"
        ) from err
    except (smtplib.SMTPException, OSError) as err:
        raise GoogleTaskNotificationError(
            f"Failed to send email notification: {err}"
        ) from err
    except socket.TimeoutError as err:
        raise GoogleTaskNotificationError(
            f"SMTP connection timed out after {SMTP_TIMEOUT} seconds"
        ) from err
    except Exception:
        _LOGGER.exception("Error: Email not sent!!")
        _LOGGER.info(
            "Email notification sent successfully to %s with %d task(s)",
            email_config["recipient_email"],
            task_count,
        )
    finally:
        if server is not None:
            try:
                server.quit()
            except smtplib.SMTPException:
                _LOGGER.warning("Failed to close SMTP server connection properly")
