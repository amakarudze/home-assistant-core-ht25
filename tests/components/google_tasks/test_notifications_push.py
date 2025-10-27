"""Tests for Google Tasks Pushbullet notification functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.google_tasks.notifications_push import (
    send_pushbullet_notification,
)


class TestPushNotification:
    """Test push notification functionality."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        return MagicMock()

    @pytest.fixture
    def mock_config_entry(self):
        """Create a mock config entry with push options."""
        config_entry = MagicMock()
        config_entry.options = {
            "access_token": "test_token_123",
            "api_endpoint": "https://api.pushbullet.com/v2/pushes",
        }
        return config_entry

    @pytest.mark.asyncio
    async def test_send_pushbullet_notification_success(self, mock_config_entry):
        """Test successful Pushbullet notification sending."""
        task_list = ["Task 1", "Task 2"]

        with patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
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
