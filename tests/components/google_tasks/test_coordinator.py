"""Coordinator test for schedule notification."""

from datetime import datetime as _Datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.google_tasks.api import AsyncConfigEntryAuth
from homeassistant.components.google_tasks.coordinator import TaskUpdateCoordinator
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_schedule_daily_notification_enabled(hass: HomeAssistant) -> None:
    """Schedules at the right time and triggers callback when the timer fires."""

<<<<<<< HEAD
    # Freeze the coordinator's datetime.datetime.now() at 2025-01-01 13:00 (naive)
=======
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
    frozen_now = _Datetime(2025, 1, 1, 13, 0, 0)

    class FixedDateTime(_Datetime):  # override now() used inside the module
        @classmethod
        def now(cls, tz=None):
            return frozen_now

<<<<<<< HEAD
    # Config: enabled at 13:30, type email
=======
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
    config_entry = MagicMock()
    config_entry.options = {
        "notification_enabled": True,
        "notification_time": "13:30",
        "notification_type": "email",
    }

    api = AsyncMock(spec=AsyncConfigEntryAuth)

<<<<<<< HEAD
    # Patch scheduler + module datetime; also patch the coordinator's internal callback
    with patch(
        "homeassistant.components.google_tasks.coordinator.async_track_point_in_time"
    ) as mock_track, patch(
        "homeassistant.components.google_tasks.coordinator.datetime.datetime",
        FixedDateTime,
    ), patch.object(
        TaskUpdateCoordinator, "_notification_callback", new_callable=AsyncMock
    ) as mock_cb:
=======
    with (
        patch(
            "homeassistant.components.google_tasks.coordinator.async_track_point_in_time"
        ) as mock_track,
        patch(
            "homeassistant.components.google_tasks.coordinator.datetime.datetime",
            FixedDateTime,
        ),
        patch.object(
            TaskUpdateCoordinator, "_notification_callback", new_callable=AsyncMock
        ) as mock_cb,
    ):
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
        coordinator = TaskUpdateCoordinator(
            hass=hass,
            config_entry=config_entry,
            api=api,
            task_list_id="list_1",
            task_list_title="My Tasks",
        )

        # Act: schedule
        await coordinator.schedule_daily_notification()

<<<<<<< HEAD
        # Assert: scheduled exactly once with expected args
=======
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
        mock_track.assert_called_once()
        args, _ = mock_track.call_args
        called_hass, scheduled_cb, target_time = args

        assert called_hass is hass
        assert callable(scheduled_cb)
        expected_target = _Datetime(2025, 1, 1, 13, 30, 0)
        assert target_time == expected_target

<<<<<<< HEAD
        # The internal callback shouldn't be called yet (it's scheduled)
        assert mock_cb.await_count == 0

        # Simulate the timer firing
        await scheduled_cb(target_time)

        # Now the coordinator's callback should have been awaited once with the same target
=======
        assert mock_cb.await_count == 0

        await scheduled_cb(target_time)

>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
        mock_cb.assert_awaited_once()
        (actual_target,), _ = mock_cb.await_args
        assert actual_target == expected_target
