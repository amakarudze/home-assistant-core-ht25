"""Constants for the Google Tasks integration."""

from enum import StrEnum

# Domain name for the integration
DOMAIN = "google_tasks"

# OAuth2 endpoints
OAUTH2_AUTHORIZE = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH2_TOKEN = "https://oauth2.googleapis.com/token"

# Scopes required for API access
OAUTH2_SCOPES = [
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/userinfo.profile",
    "openid",
]


# ---- Task status options ----
class TaskStatus(StrEnum):
    """Status of a Google Task."""

    NEEDS_ACTION = "needsAction"
    COMPLETED = "completed"


# ---- Notification configuration keys ----
CONF_NOTIFICATION_ENABLED = "notification_enabled"
CONF_NOTIFICATION_SERVICE = "notification_service"
CONF_NOTIFICATION_TIME = "notification_time"
CONF_NOTIFICATION_METHOD = "notification_method"  # NEW — Push or Email


# ---- Notification method constants ----
NOTIFICATION_METHOD_PUSH = "push"
NOTIFICATION_METHOD_EMAIL = "email"


# ---- Default values ----
DEFAULT_NOTIFICATION_ENABLED = False
DEFAULT_NOTIFICATION_SERVICE = "persistent_notification"
DEFAULT_NOTIFICATION_TIME = "08:00"
DEFAULT_NOTIFICATION_METHOD = NOTIFICATION_METHOD_PUSH

# ---- SMTP / Email Configuration Keys ----
CONF_EMAIL_ENABLED = "email_enabled"
CONF_EMAIL_SENDER = "email_sender"
CONF_EMAIL_RECIPIENT = "email_recipient"
CONF_EMAIL_SERVER = "email_server"
CONF_EMAIL_PORT = "email_port"
CONF_EMAIL_USERNAME = "email_username"
CONF_EMAIL_PASSWORD = "email_password"
