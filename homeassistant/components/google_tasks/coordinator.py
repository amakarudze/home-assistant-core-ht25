"""Coordinator for fetching data from Google Tasks API."""

import asyncio
import datetime
from datetime import date, time as dt_time, timedelta
import logging
from typing import Any, Final

from dateutil.parser import isoparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import AsyncConfigEntryAuth
from .const import DOMAIN
from .notifications_email import async_send_email_notification
from .notifications_push import async_send_pushbullet_notification

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
        self._notification_type = self.config_entry.options.get("notification_type")
        self._notify_enabled = notify_enabled
        self._notify_time = dt_time(8, 0)  # default
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

    async def get_daily_todo_tasks(self, hass: HomeAssistant) -> list[str] | None:
        """Return a list of Google Tasks due today (from all coordinators)."""
        integration_data = hass.data.get(DOMAIN, {})
        all_tasks = []

        for entry_id, entry_data in integration_data.items():
            if isinstance(entry_data, dict) and "coordinators" in entry_data:
                for coord in entry_data["coordinators"]:
                    if hasattr(coord, "data") and coord.data:
                        all_tasks.extend(coord.data)

        today = date.today()
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

    async def schedule_daily_notification(self):
        """Schedules daily execution of fetchTaskandSendNotif()."""
        print(
            "In schedule_daily_notification and notify enabled flag is %s",
            self._notify_enabled,
        )
        if not self._notify_enabled:
            return
        await self._schedule_daily_notification()

    async def _schedule_daily_notification(self):
        """Private function that schedules daily execution of fetchTaskandSendNotif()."""
        now = datetime.datetime.now()
        target = datetime.datetime.combine(now.date(), self._notify_time)

        if target <= now:
            target += timedelta(days=1)

        # async_track_point_in_time(self.hass, self._notification_callback, target)
        print("In _schedule_daily_notification and target time is %s", target)
        await self._notification_callback(target)

    async def _notification_callback(self, now):
        """Fetch daily tasks and reschedule."""
        try:
            task_list = self.get_daily_todo_tasks()
            print("In _notification_callback and task list is %s", task_list)
            if self._notification_type == "email":
                await async_send_email_notification(
                    self.hass, self.config_entry, task_list
                )
                _LOGGER.info("I am in email block")
            if self._notification_type == "push":
                await async_send_pushbullet_notification(
                    self.hass, self.config_entry, task_list
                )
                _LOGGER.info("I am in push block")

            _LOGGER.info("My callback function ")
        except Exception:
            _LOGGER.exception("My exception block")

        await self.schedule_daily_notification()
