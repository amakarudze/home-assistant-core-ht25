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

    # Patch module datetime and intercept the internal callback
    with patch(
        "homeassistant.components.google_tasks.coordinator.datetime.datetime",
        FixedDateTime,
    ), patch.object(
        TaskUpdateCoordinator, "_notification_callback", new_callable=AsyncMock
    ) as mock_cb:
        coordinator = TaskUpdateCoordinator(
            hass=hass,
            config_entry=config_entry,
            api=api,
            task_list_id="list_1",
            task_list_title="My Tasks",
        )

        await coordinator.schedule_daily_notification()

        expected_target = _Datetime(2025, 1, 1, 13, 30, 0)
        mock_cb.assert_awaited_once()
        (actual_target,), _ = mock_cb.await_args
        assert actual_target == expected_target

        # Calling schedule again triggers another immediate callback in current impl
        await coordinator.schedule_daily_notification()
        assert mock_cb.await_count == 2

        # (Optional) check both call times
        # first_call_target = mock_cb.await_args_list[0].args[0]
        # second_call_target = mock_cb.await_args_list[1].args[0]
        # assert first_call_target == expected_target
        # assert second_call_target == expected_target
