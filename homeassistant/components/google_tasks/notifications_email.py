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
        email_config:Dictonary containing email configuration with keys:
        -sender_email: Email address to send from
        -recipient_email: Email address to send to
        -sender_password: Password for the sender email account

    Raises:
        GoogleTaskNotificationError: If email sending fails.
    """

    # Validate input parameters
    if not task_list:
        _LOGGER.warning("Task list is empty. No email sent.")
        return

    if not email_config:
        raise GoogleTaskNotificationError("Email configuration is missing.")
    # Validate required email config fields
    required_fields = [
        "sender_email",
        "recipient_email",
        "sender_password",
    ]  # Use constants instead when defination is done
    missing_fields = [field for field in required_fields if not email_config.get(field)]
    if missing_fields:
        raise GoogleTaskNotificationError(
            f"Missing required email configuration fields: {', '.join(missing_fields)}"
        )

    # Get SMTP settings
    # To be added
    # For testing now,will be received from user
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
    msg["Subject"] = "Daily Reminder"

    task_count = len(task_list)
    body_lines = [
        "Hi User/Username,",
        "Gentle Reminder!",
        f"Here are your {task_count} to-do items for today:",
        "",
    ]
    body_lines.append("Best Wishes,")
    body_lines.append("Home Assistant")
    body_lines.extend([f"- {task}" for task in task_list])
    body = "\n".join(body_lines)
    msg.attach(MIMEText(body, "plain"))

    # Send email with error handling
    server = None
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_config["sender_email"], email_config["sender_password"])
        server.sendmail(
            email_config["sender_email"],
            email_config["recipient_email"],
            msg.as_string(),
        )
        _LOGGER.info(
            "Email notifacation sent successfully to %s with %d task(s).",
            email_config["recipient_email"],
            task_count,
        )
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
    finally:
        if server is not None:
            try:
                server.quit()
            except smtplib.SMTPException:
                _LOGGER.warning("Failed to close SMTP server connection properly.")


""""
 For testing only

 SENDER_EMAIL = "meenu2411as@gmail.com"
 SENDER_PASSWORD = "nchk yflh zmdh ybdz"
 RECIPIENT_EMAIL = "meaa24@student.bth.se"

 if __name__ == "__main__":
     email_config = {
         "sender_email": "meenu2411as@gmail.com",
         "sender_password": "nchk yflh zmdh ybdz",
         "recipient_email": "meaa24@student.bth.se",
     }

     task_list = ["Doctor's appointment at 3pm", "Finish HA integration"]

     send_email_notification(task_list, email_config)
"""
