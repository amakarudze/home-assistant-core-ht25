"""Coordinator for fetching data from Google Tasks API."""

import asyncio
import datetime
from datetime import time as dt_time, date, timedelta
import logging
from typing import Any, Final

from dateutil.parser import isoparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import AsyncConfigEntryAuth
from .const import DOMAIN
from .notifications_email import send_email_notification
from .notifications_push import send_pushbullet_notification

__all__ = ["DOMAIN"]
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
        notify_enabled = self.config_entry.options.get("notification_enabled", False)
        self._unsub_callback = None
        self._notification_type = self.config_entry.options.get("notification_type")
        self._notify_enabled = notify_enabled
        self._notify_time = dt_time(8, 0)  # default
        self.integration_data = hass.data.get(DOMAIN, {})
        time_str = self.config_entry.options.get("notification_time")
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

    def _extract_tasks(self):
        """Get tasks from task lists from all coordinators."""
        tasks = []
        for entry_data in self.integration_data.values():
            coordinators = (
                entry_data.get("coordinators") if isinstance(entry_data, dict) else None
            )
            if not coordinators:
                continue
            for coord in coordinators:
                if getattr(coord, "data", None):
                    tasks.extend(coord.data)
        return tasks

    def _parse_due_date(self, task):
        """Safely parse a task's due date."""
        due_str = task.get("due")
        if not due_str:
            return None
        try:
            return isoparse(due_str).date()
        except Exception:
            _LOGGER.exception(
                "Skipping invalid due date '%s' for task '%s'",
                due_str,
                task.get("title"),
            )
            return None

    def get_daily_todo_tasks(self):
        """Return a list of Google Tasks due today (from all coordinators)."""
        today = date.today()
        all_tasks = self._extract_tasks()
        due_today = []
        for task in all_tasks:
            due_date = self._parse_due_date(task)
            if due_date == today and task.get("status") != "completed":
                due_today.append(task.get("title", ""))
        return due_today

    async def schedule_daily_notification(self):
        """Schedules daily notification if enabled in config entry options."""
        if not self._notify_enabled:
            return
        await self._schedule_daily_notification()

    async def _schedule_daily_notification(self):
        """Private function that schedules the daily notification callback."""
        now = datetime.datetime.now()
        target = datetime.datetime.combine(now.date(), self._notify_time)

        if target <= now:
            target += timedelta(days=1)
        if self._unsub_callback:
            _LOGGER.debug("Cancelling previous scheduled callback")
            self._unsub_callback()
            self._unsub_callback = None

        self._unsub_callback = async_track_point_in_time(
            self.hass, self._notification_callback, target
        )

    async def _notification_callback(self, now):
        """Fetch daily tasks and sends notification and reschedules scheduler."""
        try:
            _LOGGER.info(
                "Notification Scheduler got triggered!! Attempting to send daily notification"
            )
            task_list = self.get_daily_todo_tasks()
            if self._notification_type == "email":
                send_email_notification(
                    self.config_entry, task_list
                )
            if self._notification_type == "push":
                await send_pushbullet_notification(
                    self.config_entry, task_list
                )

        except Exception:
            _LOGGER.exception("An exception occurred while sending notification")

        await self.schedule_daily_notification()
