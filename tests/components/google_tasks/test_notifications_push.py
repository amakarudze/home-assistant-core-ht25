"""Tests for Google Tasks Pushbullet notification functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Import shim: prefer async_send_pushbullet_notification; if absent, wrap the 2-arg
# send_pushbullet_notification(config_entry, task_list) to match the 3-arg signature.
try:
    from homeassistant.components.google_tasks.notifications_push import (
        async_send_pushbullet_notification,
    )
except ImportError:
    from homeassistant.components.google_tasks.notifications_push import (
        send_pushbullet_notification as _send_pushbullet_notification,
    )

    async def async_send_pushbullet_notification(hass, config_entry, task_list):
        # hass is intentionally unused; maintain backward-compatible signature for tests
        return await _send_pushbullet_notification(config_entry, task_list)


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
    async def test_send_pushbullet_notification_success(
        self, mock_hass, mock_config_entry
    ):
        """Test successful Pushbullet notification sending."""
        task_list = ["Task 1", "Task 2"]

        with patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as mock_session:
            # Setup nested async context managers
            mock_response = AsyncMock()
            mock_response.status = 200

            mock_session_instance = AsyncMock()
            mock_session.return_value = mock_session_instance
            mock_session_instance.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            await async_send_pushbullet_notification(
                mock_hass, mock_config_entry, task_list
            )

            # Verify the API call was made
            mock_session_instance.__aenter__.return_value.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_pushbullet_missing_access_token(self, mock_hass):
        """Test Pushbullet notification with missing access token."""
        task_list = ["Task 1"]
        config_entry = MagicMock()
        config_entry.options = {}

        with patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as mock_session:
            await async_send_pushbullet_notification(mock_hass, config_entry, task_list)

            # Should return early without making API call
            mock_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_pushbullet_api_error(self, mock_hass, mock_config_entry):
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

            # Should not raise exception, just log error
            await async_send_pushbullet_notification(
                mock_hass, mock_config_entry, task_list
            )

    @pytest.mark.asyncio
    async def test_pushbullet_network_error(self, mock_hass, mock_config_entry):
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

            # Should not raise exception, just log error
            await async_send_pushbullet_notification(
                mock_hass, mock_config_entry, task_list
            )

# --- Additional tests (same function/signature as above) ---

@pytest.mark.asyncio
async def test_pushbullet_endpoint_headers_and_payload_are_correct():
    """Endpoint URL, headers, and payload formatting are correct."""
    mock_hass = MagicMock()
    config_entry = MagicMock()
    config_entry.options = {
        "access_token": "tok123",
        "api_endpoint": "https://api.pushbullet.com/v2/pushes",
    }
    task_list = ["One", "Two", "Three"]

    with patch(
        "homeassistant.components.google_tasks.notifications_push.ClientSession"
    ) as Session:
        resp = MagicMock()
        resp.status = 200

        # Build a session whose post() is an async CM returning resp
        session = MagicMock()
        post_cm = MagicMock()
        post_cm.__aenter__ = AsyncMock(return_value=resp)
        post_cm.__aexit__ = AsyncMock(return_value=None)
        session.post = MagicMock(return_value=post_cm)
        Session.return_value.__aenter__.return_value = session

        await async_send_pushbullet_notification(mock_hass, config_entry, task_list)

        assert session.post.call_count == 1
        (url,), kwargs = session.post.call_args
        assert url == config_entry.options["api_endpoint"]

        headers = kwargs.get("headers") or {}
        assert headers.get("Access-Token") == "tok123"
        assert headers.get("Content-Type") == "application/json"

        payload = kwargs.get("json") or {}
        assert payload.get("type") == "note"
        assert payload.get("title")
        body = payload.get("body", "")
        for t in task_list:
            assert f"- {t}" in body


@pytest.mark.asyncio
async def test_pushbullet_rate_limited_no_raise():
    """HTTP 429 is logged with body; no exception is raised."""
    mock_hass = MagicMock()
    config_entry = MagicMock()
    config_entry.options = {
        "access_token": "tok123",
        "api_endpoint": "https://api.pushbullet.com/v2/pushes",
    }
    task_list = ["Task 1"]

    with patch(
        "homeassistant.components.google_tasks.notifications_push.ClientSession"
    ) as Session:
        resp = MagicMock()
        resp.status = 429
        resp.text = AsyncMock(return_value="Too Many Requests")

        session = MagicMock()
        post_cm = MagicMock()
        post_cm.__aenter__ = AsyncMock(return_value=resp)
        post_cm.__aexit__ = AsyncMock(return_value=None)
        session.post = MagicMock(return_value=post_cm)
        Session.return_value.__aenter__.return_value = session

        # Should not raise exception
        await async_send_pushbullet_notification(mock_hass, config_entry, task_list)

