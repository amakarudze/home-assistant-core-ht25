<<<<<<< HEAD
"""Tests for Pushbullet notifications in the Google Tasks integration."""

import logging
=======
"""Tests for Google Tasks Pushbullet notification functionality."""

>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.google_tasks.notifications_push import (
    send_pushbullet_notification,
)


<<<<<<< HEAD
def make_session_with_resp(resp: MagicMock) -> MagicMock:
    """Return a session whose POST returns an async context manager."""
    session = MagicMock()
    post_cm = MagicMock()
    post_cm.__aenter__ = AsyncMock(return_value=resp)
    post_cm.__aexit__ = AsyncMock(return_value=None)
    session.post = MagicMock(return_value=post_cm)
    return session


=======
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
class TestPushNotification:
    """Test push notification functionality."""

    @pytest.fixture
<<<<<<< HEAD
    def mock_config_entry(self) -> MagicMock:
=======
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        return MagicMock()

    @pytest.fixture
    def mock_config_entry(self):
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
        """Create a mock config entry with push options."""
        config_entry = MagicMock()
        config_entry.options = {
            "access_token": "test_token_123",
            "api_endpoint": "https://api.pushbullet.com/v2/pushes",
        }
        return config_entry

    @pytest.mark.asyncio
<<<<<<< HEAD
    async def test_send_pushbullet_notification_success(
        self, mock_config_entry: MagicMock
    ) -> None:
=======
    async def test_send_pushbullet_notification_success(self, mock_config_entry):
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
        """Test successful Pushbullet notification sending."""
        task_list = ["Task 1", "Task 2"]

        with patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
<<<<<<< HEAD
        ) as Session:
            resp = MagicMock()
            resp.status = 200
            session = make_session_with_resp(resp)
            Session.return_value.__aenter__.return_value = session

            await send_pushbullet_notification(mock_config_entry, task_list)

            assert session.post.call_count == 1

    @pytest.mark.asyncio
    async def test_pushbullet_missing_access_token(self) -> None:
        """Test Pushbullet notification with missing access token."""
        task_list = ["Task 1"]
        config_entry = MagicMock()
        config_entry.options = {}  # no access_token

        with patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as Session:
            await send_pushbullet_notification(config_entry, task_list)
            Session.assert_not_called()

    @pytest.mark.asyncio
    async def test_pushbullet_api_error(
        self, mock_config_entry: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test Pushbullet API error handling."""
        task_list = ["Task 1"]

        with caplog.at_level("ERROR"), patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as Session:
            resp = MagicMock()
            resp.status = 400
            resp.text = AsyncMock(return_value="Bad Request")

            session = make_session_with_resp(resp)
            Session.return_value.__aenter__.return_value = session

            await send_pushbullet_notification(mock_config_entry, task_list)

            assert any(
                r.levelno == logging.ERROR
                and "Failed to send Pushbullet notification [400]" in r.message
                for r in caplog.records
            )

    @pytest.mark.asyncio
    async def test_pushbullet_network_error(
        self, mock_config_entry: MagicMock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test Pushbullet network error handling."""
        task_list = ["Task 1"]

        with caplog.at_level("ERROR"), patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as Session:
            session = MagicMock()
            post_cm = MagicMock()
            post_cm.__aenter__ = AsyncMock(side_effect=Exception("Network error"))
            post_cm.__aexit__ = AsyncMock(return_value=None)
            session.post = MagicMock(return_value=post_cm)
            Session.return_value.__aenter__.return_value = session

            await send_pushbullet_notification(mock_config_entry, task_list)

            assert any(
                r.levelno == logging.ERROR
                and "Error sending Pushbullet notification" in r.message
                for r in caplog.records
            )
=======
        ) as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200

            mock_session_instance = AsyncMock()
            mock_session.return_value = mock_session_instance
            mock_session_instance.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            await send_pushbullet_notification(mock_config_entry, task_list)

            mock_session_instance.__aenter__.return_value.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_pushbullet_missing_access_token(self):
        """Test Pushbullet notification with missing access token."""
        task_list = ["Task 1"]
        config_entry = MagicMock()
        config_entry.options = {}

        with patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as mock_session:
            await send_pushbullet_notification(config_entry, task_list)

            mock_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_pushbullet_api_error(self, mock_config_entry):
        """Test Pushbullet API error handling."""
        task_list = ["Task 1"]

        with patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.text.return_value = "Bad Request"

            mock_session_instance = AsyncMock()
            mock_session.return_value = mock_session_instance
            mock_session_instance.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            await send_pushbullet_notification(mock_config_entry, task_list)

    @pytest.mark.asyncio
    async def test_pushbullet_network_error(self, mock_config_entry):
        """Test Pushbullet network error handling."""
        task_list = ["Task 1"]

        with patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as mock_session:
            mock_session_instance = AsyncMock()
            mock_session.return_value = mock_session_instance
            mock_session_instance.__aenter__.return_value.post.side_effect = Exception(
                "Network error"
            )

            await send_pushbullet_notification(mock_config_entry, task_list)
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
