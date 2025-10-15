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
CONF_NOTIFY_ENABLED = "notify_enabled"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_NOTIFY_TIME = "notify_time"
CONF_NOTIFY_METHOD = "notify_method"  # NEW — Push or Email


# ---- Notification method constants ----
NOTIFY_METHOD_PUSH = "push"
NOTIFY_METHOD_EMAIL = "email"


# ---- Default values ----
DEFAULT_NOTIFY_ENABLED = False
DEFAULT_NOTIFY_SERVICE = "persistent_notification"
DEFAULT_NOTIFY_TIME = "08:00"
DEFAULT_NOTIFY_METHOD = NOTIFY_METHOD_PUSH

# ---- SMTP / Email Configuration Keys ----
CONF_EMAIL_ENABLED = "email_enabled"
CONF_EMAIL_SENDER = "email_sender"
CONF_EMAIL_RECIPIENT = "email_recipient"
CONF_EMAIL_SERVER = "email_server"
CONF_EMAIL_PORT = "email_port"
CONF_EMAIL_USERNAME = "email_username"
CONF_EMAIL_PASSWORD = "email_password"
