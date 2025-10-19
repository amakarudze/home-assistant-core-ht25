"""The Google Tasks integration with custom Pushbullet and Email notifications."""

from __future__ import annotations

import asyncio
from datetime import datetime 
import aiohttp
from aiohttp import ClientError, ClientResponseError, ClientSession
import aiosmtplib
from email.mime.text import MIMEText
from dateutil.parser import isoparse

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.event import async_track_time_change
import logging

from . import api
from .const import (
    DOMAIN,
    CONF_NOTIFY_ENABLED,
    CONF_NOTIFY_TIME,
    CONF_NOTIFY_METHOD,
    CONF_PUSHBULLET_API_KEY,
    CONF_EMAIL_SENDER,
    CONF_EMAIL_PASSWORD,
    CONF_EMAIL_RECIPIENT,
    CONF_EMAIL_SERVER,
    CONF_EMAIL_PORT,
    NOTIFY_METHOD_PUSH,
    NOTIFY_METHOD_EMAIL,
)
from .coordinator import GoogleTasksConfigEntry, TaskUpdateCoordinator
from .exceptions import GoogleTasksApiError

__all__ = ["DOMAIN"]
_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.TODO]


async def async_setup_entry(hass: HomeAssistant, entry: GoogleTasksConfigEntry) -> bool:
    """Set up Google Tasks from a config entry."""
    _LOGGER.info("Setting up Google Tasks integration")

    implementation = await config_entry_oauth2_flow.async_get_config_entry_implementation(
        hass, entry
    )
    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    auth = api.AsyncConfigEntryAuth(hass, session)

    # ---- Authenticate ----
    try:
        await auth.async_get_access_token()
    except ClientResponseError as err:
        if 400 <= err.status < 500:
            raise ConfigEntryAuthFailed("OAuth session invalid, reauth required") from err
        raise ConfigEntryNotReady from err
    except ClientError as err:
        raise ConfigEntryNotReady from err

    # ---- Get task lists ----
    try:
        task_lists = await auth.list_task_lists()
    except GoogleTasksApiError as err:
        raise ConfigEntryNotReady from err

    # ---- Create coordinators ----
    coordinators = [
        TaskUpdateCoordinator(hass, entry, auth, task_list["id"], task_list["title"])
        for task_list in task_lists
    ]

    await asyncio.gather(
        *(coordinator.async_config_entry_first_refresh() for coordinator in coordinators)
    )

    entry.runtime_data = coordinators
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinators": coordinators}

    # ---- Forward platform setup ----
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # ---- Notifications ----
    options = entry.options
    notify_enabled = options.get(CONF_NOTIFY_ENABLED, False)
    notify_time = options.get(CONF_NOTIFY_TIME)
    notify_method = options.get(CONF_NOTIFY_METHOD, NOTIFY_METHOD_PUSH)

    if notify_enabled:
        try:
            hour, minute = map(int, notify_time.split(":"))
        except ValueError:
            hour, minute = 8, 0

        async def send_daily_task_notification(now):
            """Send a daily summary of tasks due today."""
            tasks = await get_due_today_tasks(hass)
            _LOGGER.info("Tasks due today: %s", tasks)
            if not tasks:
                _LOGGER.info("No tasks due today. Skipping notification.")
                return

            title = "Google Tasks - Daily Summary"
            message = "Today's Google Tasks:\n" + "\n".join(f"- {t}" for t in tasks)

            if notify_method == NOTIFY_METHOD_PUSH:
                await async_send_pushbullet_notification(hass, options, title, message)
            elif notify_method == NOTIFY_METHOD_EMAIL:
                await async_send_email_notification(hass, options, title, message)

            _LOGGER.info("Notification sent for %d tasks.", len(tasks))



        # Schedule daily notification
        async_track_time_change(
            hass,
            send_daily_task_notification,
            hour=hour,
            minute=minute,
            second=0,
        )



# Register manual trigger service
        async def handle_trigger_daily_notification(call):
            """Manually trigger the daily task notification."""
            _LOGGER.info("Manual trigger of daily task notification")
            await send_daily_task_notification(None)

        hass.services.async_register(
            DOMAIN,
            "trigger_daily_task_notification",
            handle_trigger_daily_notification
        )

    return True

        # --- TEMPORARY: trigger immediately for push notification testing ---
        #--- hass.async_create_task(send_daily_task_notification(None))---
        #return True
        
        


async def async_send_pushbullet_notification(hass, options, title, message):
    """Send a Pushbullet notification."""
    api_key = options.get(CONF_PUSHBULLET_API_KEY)
    if not api_key:
        _LOGGER.warning("Pushbullet API key not set; skipping notification.")
        return

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                "https://api.pushbullet.com/v2/pushes",
                headers={
                    "Access-Token": api_key,
                    "Content-Type": "application/json",
                },
                json={"type": "note", "title": title, "body": message},
            ) as resp:
                if resp.status != 200:
                    _LOGGER.error(
                        "Failed to send Pushbullet notification [%s]: %s",
                        resp.status,
                        await resp.text(),
                    )
                else:
                    _LOGGER.info("Pushbullet notification sent successfully.")
        except Exception as err:
            _LOGGER.error("Error sending Pushbullet notification: %s", err)






async def async_send_email_notification(hass, options, title, message):
    """Send an email notification via SMTP."""
    sender = options.get(CONF_EMAIL_SENDER)
    password = options.get(CONF_EMAIL_PASSWORD)
    recipient = options.get(CONF_EMAIL_RECIPIENT)
    server = options.get(CONF_EMAIL_SERVER, "smtp.gmail.com")
    port = options.get(CONF_EMAIL_PORT, 587)

    if not (sender and password and recipient):
        _LOGGER.warning("Email credentials or recipient missing; skipping email.")
        return

    mime_msg = MIMEText(message)
    mime_msg["From"] = sender
    mime_msg["To"] = recipient
    mime_msg["Subject"] = title

    try:
        await aiosmtplib.send(
            mime_msg,
            hostname=server,
            port=port,
            start_tls=True,
            username=sender,
            password=password,
        )
        _LOGGER.info("Email notification sent successfully.")
    except Exception as err:
        _LOGGER.error("Failed to send email: %s", err)
        print("email notification failed")



async def get_due_today_tasks(hass: HomeAssistant) -> list[str]:
    """Return a list of Google Tasks due today (from all coordinators)."""
    integration_data = hass.data.get(DOMAIN, {})
    all_tasks = []

    for entry_id, entry_data in integration_data.items():
        if isinstance(entry_data, dict) and "coordinators" in entry_data:
            for coord in entry_data["coordinators"]:
                if hasattr(coord, "data") and coord.data:
                    all_tasks.extend(coord.data)

    today = datetime.now().date()
    due_today: list[str] = []

    for task in all_tasks:
        due_str = task.get("due")
        if not due_str:
            continue
        try:
            due_date = isoparse(due_str).date()
        except Exception as err:
            _LOGGER.warning(
                "Failed to parse due date '%s' for task '%s': %s",
                due_str,
                task.get("title"),
                err,
            )
            continue
        if due_date == today and task.get("status") != "completed":
            due_today.append(task.get("title", ""))



    return due_today


async def async_unload_entry(hass: HomeAssistant, entry: GoogleTasksConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
