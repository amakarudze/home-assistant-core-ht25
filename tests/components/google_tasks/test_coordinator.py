"""Coordinator test for schedule notification."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.google_tasks.api import AsyncConfigEntryAuth
from homeassistant.components.google_tasks.coordinator import TaskUpdateCoordinator
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_schedule_daily_notification_enabled(hass: HomeAssistant) -> None:

    """Schedules at the right time and triggers callback when the timer fires."""

    # Freeze the coordinator's datetime.datetime.now() at 2025-01-01 13:00 (naive)
    config_entry = MagicMock()
    config_entry.options = {
        "notification_enabled": True,
        "notification_type": "email",
    }

    # Mock API
    api = AsyncMock(spec=AsyncConfigEntryAuth)

    # Patch async_track_point_in_time so it doesn't schedule real callbacks
    with patch(
        "homeassistant.components.google_tasks.coordinator.async_track_point_in_time"
    ) as mock_track:
        coordinator = TaskUpdateCoordinator(
            hass=hass,
            config_entry=config_entry,
            api=api,
            task_list_id="list_1",
            task_list_title="My Tasks",
        )

        # Act: schedule
        await coordinator.schedule_daily_notification()

        # Assert: scheduled exactly once with expected args
        mock_track.assert_called_once()
        args, _ = mock_track.call_args
        called_hass, scheduled_cb, target_time = args

        assert called_hass is hass
        assert callable(scheduled_cb)
        expected_target = _Datetime(2025, 1, 1, 13, 30, 0)
        assert target_time == expected_target

