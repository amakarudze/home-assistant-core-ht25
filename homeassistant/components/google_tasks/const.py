"""Constants for the Google Tasks integration."""

from enum import StrEnum

# ---- Domain ----
DOMAIN = "google_tasks"

# ---- OAuth2 ----
OAUTH2_AUTHORIZE = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH2_TOKEN = "https://oauth2.googleapis.com/token"

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

# ---- Notification configuration ----
CONF_NOTIFY_ENABLED = "notify_enabled"
CONF_NOTIFY_TIME = "notify_time"
CONF_NOTIFY_METHOD = "notify_method"  # push/email

# ---- Notification methods ----
NOTIFY_METHOD_PUSH = "push"
NOTIFY_METHOD_EMAIL = "email"

# ---- Pushbullet ----
CONF_PUSHBULLET_API_KEY = "pushbullet_api_key"

# ---- Email (SMTP) ----
CONF_EMAIL_SENDER = "email_sender"
CONF_EMAIL_PASSWORD = "email_password"
CONF_EMAIL_RECIPIENT = "email_recipient"
CONF_EMAIL_SERVER = "email_server"
CONF_EMAIL_PORT = "email_port"

# ---- Defaults ----
DEFAULT_NOTIFY_ENABLED = False
DEFAULT_NOTIFY_TIME = "08:00"
DEFAULT_NOTIFY_METHOD = NOTIFY_METHOD_PUSH
DEFAULT_EMAIL_SERVER = "smtp.gmail.com"
DEFAULT_EMAIL_PORT = 587
