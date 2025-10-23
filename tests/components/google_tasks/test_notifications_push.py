"""Tests for Google Tasks Pushbullet notification functionality."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.google_tasks.notifications_push import (
    send_pushbullet_notification,
)


def make_session_with_resp(resp):
    """Build a mocked aiohttp ClientSession.

    The returned `session` has `session.post(...)` that yields an async context
    manager which returns `resp` on `__aenter__`.
    """
    session = MagicMock()
    post_cm = MagicMock()
    post_cm.__aenter__ = AsyncMock(return_value=resp)
    post_cm.__aexit__ = AsyncMock(return_value=None)
    session.post = MagicMock(return_value=post_cm)
    return session


class TestPushNotification:
    """Test push notification functionality."""

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
        """Successful Pushbullet notification sends exactly one POST."""
        task_list = ["Task 1", "Task 2"]

        with patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as Session:
            resp = MagicMock()
            resp.status = 200
            session = make_session_with_resp(resp)
            Session.return_value.__aenter__.return_value = session

            await send_pushbullet_notification(mock_config_entry, task_list)

            assert session.post.call_count == 1

    @pytest.mark.asyncio
    async def test_pushbullet_missing_access_token(self):
        """Missing access token short-circuits without creating a session."""
        task_list = ["Task 1"]
        config_entry = MagicMock()
        config_entry.options = {}  # no access_token

        with patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as Session:
            await send_pushbullet_notification(config_entry, task_list)
            Session.assert_not_called()

    @pytest.mark.asyncio
    async def test_pushbullet_api_error(self, mock_config_entry, caplog):
        """HTTP 400 logs an error but does not raise."""
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
    async def test_pushbullet_network_error(self, mock_config_entry, caplog):
        """Network exception inside POST context logs an error."""
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


@pytest.mark.asyncio
async def test_pushbullet_endpoint_headers_and_payload_are_correct():
    """Endpoint URL, headers, and payload formatting are correct."""
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

        session = make_session_with_resp(resp)
        Session.return_value.__aenter__.return_value = session

        await send_pushbullet_notification(config_entry, task_list)

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
async def test_pushbullet_rate_limited_no_raise(caplog):
    """HTTP 429 is logged with body; no exception is raised."""
    config_entry = MagicMock()
    config_entry.options = {
        "access_token": "tok123",
        "api_endpoint": "https://api.pushbullet.com/v2/pushes",
    }
    task_list = ["Task 1"]

    with caplog.at_level("ERROR"), patch(
        "homeassistant.components.google_tasks.notifications_push.ClientSession"
    ) as Session:
        resp = MagicMock()
        resp.status = 429
        resp.text = AsyncMock(return_value="Too Many Requests")

        session = make_session_with_resp(resp)
        Session.return_value.__aenter__.return_value = session

        await send_pushbullet_notification(config_entry, task_list)

        assert any(
            r.levelno == logging.ERROR
            and "Failed to send Pushbullet notification [429]: Too Many Requests"
            in r.message
            for r in caplog.records
        )
