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
from .notifications_email import send_email_notification
from .todo import GoogleTaskTodoEntity as todo

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

    # Logic for scheduling daily notification
    async def schedule_daily_notification(self):
        """Schedules daily execution of schedule_daily_notification()."""
        # print("I am in first calling function of scheduler")
        # print("Notify enabled flag is ", self._notify_enabled)
        if not self._notify_enabled:
            return
        await self._schedule_daily_notification()

    async def _schedule_daily_notification(self):
        """Private function that schedules daily execution of _schedule_daily_notification()."""
        # print("I am in second calling function of scheduler")
        now = datetime.datetime.now()
        # print("Date Time now is ", now)
        target = datetime.datetime.combine(now.date(), self._notify_time)
        # print("Target Scheduler time is ", target)

        if target <= now:
            target += timedelta(days=1)
            # print("New Target Scheduler time is ", target)

        async_track_point_in_time(self.hass, self._notification_callback, target)

    async def _notification_callback(self, now):
        """Run _notification_callback and reschedule."""
        try:
            task_list = todo.get_daily_todo_items()
            if self._notification_type == "email":
                await notification.send_email_notification(hass, config_entry, task_list )
                _LOGGER.info("I am in email block")
            if self._notification_type == "push":
                # await notification.send_push_notification(task_list)
                _LOGGER.info("I am in push block")
            # print("I am in third calling function of scheduler")
            # print("My scheduler is running")
            _LOGGER.info("My callback function ")
        except Exception:
            # print("Notification error")
            _LOGGER.exception("My exception block")

        # print("I am going to reset scheduler time now")
        await self.schedule_daily_notification()
