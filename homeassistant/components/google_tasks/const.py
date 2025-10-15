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

# Task status options
class TaskStatus(StrEnum):
    """Status of a Google Task."""

    NEEDS_ACTION = "needsAction"
    COMPLETED = "completed"


# ---- Notification option keys (used in config_flow and __init__.py) ----
CONF_NOTIFY_ENABLED = "notify_enabled"
CONF_NOTIFY_SERVICE = "notify_service"
CONF_NOTIFY_TIME = "notify_time"

# Default values
DEFAULT_NOTIFY_ENABLED = False
DEFAULT_NOTIFY_SERVICE = "persistent_notification"
DEFAULT_NOTIFY_TIME = "08:00"
