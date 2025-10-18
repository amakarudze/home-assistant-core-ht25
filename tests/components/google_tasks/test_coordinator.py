"""Coordinator test for schedule notification."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.google_tasks.api import AsyncConfigEntryAuth
from homeassistant.components.google_tasks.coordinator import TaskUpdateCoordinator
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_schedule_daily_notification_enabled(hass: HomeAssistant) -> None:
    """Test for scheduler."""

    # Fake config_entry with notify_enabled = True and notify_time = "08:00"
    config_entry = MagicMock()
    config_entry.options = {
        "notification_enabled": True,
        "notification_time": "13:30",
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

        await coordinator.schedule_daily_notification()
        # print("called scheduler")

        # Check async_track_point_in_time was called once
        assert mock_track.called, "async_track_point_in_time should be called"
        call_args = mock_track.call_args[0]
        assert call_args[0] == hass
        assert callable(call_args[1])
