"""The Google Tasks integration."""

from __future__ import annotations

import asyncio
from datetime import datetime
from aiohttp import ClientError, ClientResponseError

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.event import async_track_time_change

from . import api
from .const import (
    DOMAIN,
    CONF_NOTIFY_ENABLED,
    CONF_NOTIFY_SERVICE,
    CONF_NOTIFY_TIME,
)
from .coordinator import GoogleTasksConfigEntry, TaskUpdateCoordinator
from .exceptions import GoogleTasksApiError

__all__ = ["DOMAIN"]

PLATFORMS: list[Platform] = [Platform.TODO]


async def async_setup_entry(hass: HomeAssistant, entry: GoogleTasksConfigEntry) -> bool:
    """Set up Google Tasks from a config entry."""
    implementation = (
        await config_entry_oauth2_flow.async_get_config_entry_implementation(hass, entry)
    )
    session = config_entry_oauth2_flow.OAuth2Session(hass, entry, implementation)
    auth = api.AsyncConfigEntryAuth(hass, session)

    # ---- Authenticate ----
    try:
        await auth.async_get_access_token()
    except ClientResponseError as err:
        if 400 <= err.status < 500:
            raise ConfigEntryAuthFailed(
                "OAuth session invalid, reauth required"
            ) from err
        raise ConfigEntryNotReady from err
    except ClientError as err:
        raise ConfigEntryNotReady from err

    # ---- Get task lists ----
    try:
        task_lists = await auth.list_task_lists()
    except GoogleTasksApiError as err:
        raise ConfigEntryNotReady from err

    # ---- Create coordinators for each task list ----
    coordinators = [
        TaskUpdateCoordinator(
            hass,
            entry,
            auth,
            task_list["id"],
            task_list["title"],
        )
        for task_list in task_lists
    ]

    # Refresh all coordinators in parallel
    await asyncio.gather(
        *(
            coordinator.async_config_entry_first_refresh()
            for coordinator in coordinators
        )
    )
    entry.runtime_data = coordinators
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"coordinators": coordinators}

    # ---- Forward platform setup ----
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # ---- Set up notifications (from OptionsFlow) ----
    options = entry.options
    notify_enabled = options.get(CONF_NOTIFY_ENABLED, False)
    notify_service = options.get(CONF_NOTIFY_SERVICE, "persistent_notification")
    notify_time = options.get(CONF_NOTIFY_TIME, "08:00")

    if notify_enabled:
        try:
            hour, minute = map(int, notify_time.split(":"))
        except ValueError:
            hour, minute = 8, 0  # fallback

        async def send_daily_task_notification(now):
            """Send a daily summary of tasks due today."""
            tasks = await get_due_today_tasks(hass)
            if not tasks:
                return
            message = "Today's Google Tasks:\n" + "\n".join(f"- {t}" for t in tasks)
            await hass.services.async_call(
                "notify",
                notify_service,
                {"message": message, "title": "Google Tasks Reminder"},
                blocking=False,
            )

        async_track_time_change(
            hass,
            send_daily_task_notification,
            hour=hour,
            minute=minute,
            second=0,
        )

    return True


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
            due_date = datetime.fromisoformat(due_str).date()
        except Exception:
            continue
        if due_date == today and task.get("status") != "completed":
            due_today.append(task.get("title", ""))

    return due_today


async def async_unload_entry(hass: HomeAssistant, entry: GoogleTasksConfigEntry) -> bool:
    """Unload a config entry."""
    hass.data[DOMAIN].pop(entry.entry_id, None)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
