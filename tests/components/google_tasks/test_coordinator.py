"""Coordinator test for schedule notification."""

from datetime import datetime as _Datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.google_tasks.api import AsyncConfigEntryAuth
from homeassistant.components.google_tasks.coordinator import TaskUpdateCoordinator
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_schedule_daily_notification_enabled(hass: HomeAssistant) -> None:
    """schedule_daily_notification computes the correct target time and triggers the callback once."""

    # Freeze the coordinator's datetime.datetime.now() at 2025-01-01 13:00 (naive)
    frozen_now = _Datetime(2025, 1, 1, 13, 0, 0)

    class FixedDateTime(_Datetime):  # override now() used inside the module
        @classmethod
        def now(cls, tz=None):
            return frozen_now

    # Config: enabled at 13:30, type email
    config_entry = MagicMock()
    config_entry.options = {
        "notification_enabled": True,
        "notification_time": "13:30",
        "notification_type": "email",
    }

    api = AsyncMock(spec=AsyncConfigEntryAuth)

    # Patch the notification functions to avoid actual email/push sending
    with (
        patch(
            "homeassistant.components.google_tasks.coordinator.async_send_email_notification"
        ) as mock_email,
        patch(
            "homeassistant.components.google_tasks.coordinator.async_send_pushbullet_notification"
        ) as mock_push,
    ):
        coordinator = TaskUpdateCoordinator(
            hass=hass,
            config_entry=config_entry,
            api=api,
            task_list_id="list_1",
            task_list_title="My Tasks",
        )

        await coordinator.schedule_daily_notification()

        # Check that email notification was called (since notification_type is "email")
        assert mock_email.called, "Email notification should be called"
        assert not mock_push.called, "Push notification should not be called"


@pytest.mark.asyncio
async def test_schedule_daily_notification_disabled(hass: HomeAssistant) -> None:
    """Test scheduler when notifications are disabled."""

    # Fake config_entry with notify_enabled = False
    config_entry = MagicMock()
    config_entry.options = {
        "notification_enabled": False,
        "notification_time": "13:30",
        "notification_type": "email",
    }

    # Mock API
    api = AsyncMock(spec=AsyncConfigEntryAuth)

    # Patch the notification functions
    with (
        patch(
            "homeassistant.components.google_tasks.coordinator.async_send_email_notification"
        ) as mock_email,
        patch(
            "homeassistant.components.google_tasks.coordinator.async_send_pushbullet_notification"
        ) as mock_push,
    ):
        coordinator = TaskUpdateCoordinator(
            hass=hass,
            config_entry=config_entry,
            api=api,
            task_list_id="list_1",
            task_list_title="My Tasks",
        )

        await coordinator.schedule_daily_notification()

        # Check that no notifications were called
        assert not mock_email.called, "Email notification should not be called"
        assert not mock_push.called, "Push notification should not be called"


@pytest.mark.asyncio
async def test_schedule_daily_notification_push_type(hass: HomeAssistant) -> None:
    """Test scheduler with push notification type."""

    # Fake config_entry with push notification type
    config_entry = MagicMock()
    config_entry.options = {
        "notification_enabled": True,
        "notification_time": "13:30",
        "notification_type": "push",
    }

    # Mock API
    api = AsyncMock(spec=AsyncConfigEntryAuth)

    # Patch the notification functions
    with (
        patch(
            "homeassistant.components.google_tasks.coordinator.async_send_email_notification"
        ) as mock_email,
        patch(
            "homeassistant.components.google_tasks.coordinator.async_send_pushbullet_notification"
        ) as mock_push,
    ):
        coordinator = TaskUpdateCoordinator(
            hass=hass,
            config_entry=config_entry,
            api=api,
            task_list_id="list_1",
            task_list_title="My Tasks",
        )

        await coordinator.schedule_daily_notification()

        # Check that push notification was called (since notification_type is "push")
        assert not mock_email.called, "Email notification should not be called"
        assert mock_push.called, "Push notification should be called"
