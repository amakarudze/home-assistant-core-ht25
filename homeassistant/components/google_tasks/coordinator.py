"""Coordinator for fetching data from Google Tasks API."""

import asyncio
import datetime
from datetime import time as dt_time, timedelta
import logging
from typing import Any, Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import AsyncConfigEntryAuth

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL: Final = datetime.timedelta(minutes=30)
TIMEOUT = 10

type GoogleTasksConfigEntry = ConfigEntry[list[TaskUpdateCoordinator]]


class TaskUpdateCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator for fetching Google Tasks for a Task List form the API."""

    config_entry: GoogleTasksConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: GoogleTasksConfigEntry,
        api: AsyncConfigEntryAuth,
        task_list_id: str,
        task_list_title: str,
    ) -> None:
        """Initialize TaskUpdateCoordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=f"Google Tasks {task_list_id}",
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self.task_list_id = task_list_id
        self.task_list_title = task_list_title
        notify_enabled = self.config_entry.options.get("notify_enabled", False)
        self._email_config = {
            "sender_email": self.config_entry.options.get("SENDER_EMAIL"),
            "recipient_email": self.config_entry.options.get("RECIPIENT_EMAIL"),
            "sender_password": self.config_entry.options.get("SENDER_PASSWORD"),
            "port": self.config_entry.options.get("PORT"),
            "host_name": self.config_entry.options.get("HOST_NAME"),
        }
        self._access_token = self.config_entry.options.get("ACCESS_TOKEN")
        self._notify_enabled = notify_enabled
        self._notify_time = dt_time(8, 0)  # default
        time_str = self.config_entry.options.get("notify_time")
        if time_str:
            try:
                hour, minute = map(int, time_str.split(":"))
                self._notify_time = dt_time(hour, minute)
            except ValueError:
                _LOGGER.warning("Invalid notify_time format in options: %s", time_str)

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch tasks from API endpoint."""
        async with asyncio.timeout(TIMEOUT):
            return await self.api.list_tasks(self.task_list_id)

    async def schedule_daily_notification(self):
        """Schedules daily execution of fetchTaskandSendNotif()."""
        if not self._notify_enabled:
            return
        await self._schedule_daily_notification()

    async def _schedule_daily_notification(self):
        """Private function that schedules daily execution of fetchTaskandSendNotif()."""
        now = datetime.now()
        target = datetime.combine(now.date(), self._notify_time)

        if target <= now:
            target += timedelta(days=1)

        async_track_point_in_time(self._hass, self._notification_callback, target)

    async def _notification_callback(self, now):
        """Run fetchTaskandSendNotif and reschedule."""
        try:
            # fetch_Task()
            # if notification_type is Email
            # notification.send_email_notification(task_list, self._email_config )
            # if notification_type is Push
            # notification.send_email_notification(task_list, self._access_token)
            _LOGGER.info("My scheduler is running")
        except Exception:
            _LOGGER.exception("Notification error")

        self._schedule_daily_notification()
