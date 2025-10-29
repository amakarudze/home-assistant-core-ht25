"""Constants for the Google Tasks integration."""

from enum import StrEnum

DOMAIN = "google_tasks"

OAUTH2_AUTHORIZE = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH2_TOKEN = "https://oauth2.googleapis.com/token"
OAUTH2_SCOPES = [
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/userinfo.profile",
]


class TaskStatus(StrEnum):
    """Status of a Google Task."""

    NEEDS_ACTION = "needsAction"
    COMPLETED = "completed"


ACCESS_TOKEN = "access_token"
API_ENDPOINT = "api_endpoint"
NOTIFICATION_ENABLED = "notification_enabled"
NOTIFICATION_EMAIL = "email"
NOTIFICATION_PUSH = "push"
NOTIFICATION_TIME = "notification_time"
SMTP_HOST = "smtp_host"
SMTP_PORT = "smtp_port"
SMTP_USERNAME = "smtp_username"
SMTP_PASSWORD = "smtp_password"
RECIPIENT_EMAIL = "recipient_email"
