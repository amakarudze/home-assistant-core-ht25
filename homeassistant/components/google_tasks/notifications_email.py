"""Email notification handler for Google Tasks integration."""

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib

_LOGGER = logging.getLogger(__name__)


def send_email_notification(task_list, email_config):
    """Sending daily task email notification remider to the user."""

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

    try:
        server = smtplib.SMTP(email_config["host_name"], email_config["port"])
        server.starttls()
        server.login(email_config["sender_email"], email_config["sender_password"])
        server.sendmail(
            email_config["sender_email"],
            email_config["recipient_email"],
            msg.as_string(),
        )
        server.quit()
        _LOGGER.info("Email sent successfully!")
        # print("Email sent successfully!")

    except Exception:
        _LOGGER.exception("Error: Email not sent!!")
        # print("email not sent!!")


# For testing only

# SENDER_EMAIL = "meenu2411as@gmail.com"
# SENDER_PASSWORD = "nchk yflh zmdh ybdz"
# RECIPIENT_EMAIL = "meaa24@student.bth.se"

# if __name__ == "__main__":
#     email_config = {
#         "sender_email": "meenu2411as@gmail.com",
#         "sender_password": "nchk yflh zmdh ybdz",
#         "recipient_email": "meenu2411as@gmail.com",
#         "port": 587,
#         "host_name": "smtp.gmail.com",
#     }

#     task_list = ["Doctor's appointment at 3pm", "Finish HA integration"]

#     send_email_notification(task_list, email_config)
