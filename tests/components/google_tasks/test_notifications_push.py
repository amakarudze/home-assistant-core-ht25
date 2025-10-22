"""Tests for Google Tasks Pushbullet notification functionality."""

import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from homeassistant.components.google_tasks.notifications_push import (
    send_pushbullet_notification,
)


# -------------------------
# Helpers for aiohttp mocks
# -------------------------
def make_session_with_resp(resp):
    """
    Build a mocked aiohttp ClientSession that yields `session`,
    and where `session.post(...)` returns an async context manager
    yielding `resp`.
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

    # -----------------------
    # Happy-path: status 200
    # -----------------------
    @pytest.mark.asyncio
    async def test_send_pushbullet_notification_success(self, mock_config_entry):
        """Test successful Pushbullet notification sending."""
        task_list = ["Task 1", "Task 2"]

        with patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as Session:
            resp = MagicMock()
            resp.status = 200
            session = make_session_with_resp(resp)
            Session.return_value.__aenter__.return_value = session

            await send_pushbullet_notification(mock_config_entry, task_list)

            # Verify the API call was made once
            assert session.post.call_count == 1

    # -----------------------------------
    # Missing access token -> no HTTP call
    # -----------------------------------
    @pytest.mark.asyncio
    async def test_pushbullet_missing_access_token(self):
        """Test Pushbullet notification with missing access token."""
        task_list = ["Task 1"]
        config_entry = MagicMock()
        config_entry.options = {}  # no access_token

        with patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as Session:
            await send_pushbullet_notification(config_entry, task_list)
            # Should return early without making API call/session
            Session.assert_not_called()

    # ---------------------------------
    # API error (non-200, e.g., 400 Bad)
    # ---------------------------------
    @pytest.mark.asyncio
    async def test_pushbullet_api_error(self, mock_config_entry, caplog):
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

            # Should log an error, not raise
            assert any(
                r.levelno == logging.ERROR
                and "Failed to send Pushbullet notification [400]" in r.message
                for r in caplog.records
            )

    # ------------------------
    # Network error -> except
    # ------------------------
    @pytest.mark.asyncio
    async def test_pushbullet_network_error(self, mock_config_entry, caplog):
        """Test Pushbullet network error handling."""
        task_list = ["Task 1"]

        with caplog.at_level("ERROR"), patch(
            "homeassistant.components.google_tasks.notifications_push.ClientSession"
        ) as Session:
            # Raise when entering the POST context (e.g., connection/timeout)
            session = MagicMock()
            post_cm = MagicMock()
            post_cm.__aenter__ = AsyncMock(side_effect=Exception("Network error"))
            post_cm.__aexit__ = AsyncMock(return_value=None)
            session.post = MagicMock(return_value=post_cm)
            Session.return_value.__aenter__.return_value = session

            # Should not raise exception, just log error via the except path
            await send_pushbullet_notification(mock_config_entry, task_list)

            assert any(
                r.levelno == logging.ERROR
                and "Error sending Pushbullet notification" in r.message
                for r in caplog.records
            )


# -------------------------------------------------------------
# Additional high-value tests (use correct async-with mocking)
# -------------------------------------------------------------

# 1) Wiring: endpoint, headers, payload are correct
@pytest.mark.asyncio
async def test_pushbullet_endpoint_headers_and_payload_are_correct():
    config_entry = MagicMock()
    config_entry.options = {
        "access_token": "tok123",
        "api_endpoint": "https://api.pushbullet.com/v2/pushes",
    }
    task_list = ["One", "Two", "Three"]

    with patch("homeassistant.components.google_tasks.notifications_push.ClientSession") as Session:
        resp = MagicMock()
        resp.status = 200

        session = make_session_with_resp(resp)
        Session.return_value.__aenter__.return_value = session

        await send_pushbullet_notification(config_entry, task_list)

        # Verify POST call and inspect it
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


# 2) 429 rate-limited -> log error, no crash
@pytest.mark.asyncio
async def test_pushbullet_rate_limited_no_raise(caplog):
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

        # Non-200 branch should log one error with formatted status & body
        assert any(
            r.levelno == logging.ERROR
            and "Failed to send Pushbullet notification [429]: Too Many Requests" in r.message
            for r in caplog.records
        )
# 3) Empty task list -> skip (no HTTP call)
import pytest
from unittest.mock import MagicMock, patch
from homeassistant.components.google_tasks.notifications_push import send_pushbullet_notification

@pytest.mark.asyncio
async def test_pushbullet_empty_task_list_skips_call(caplog):
    config_entry = MagicMock()
    config_entry.options = {
        "access_token": "tok123",
        "api_endpoint": "https://api.pushbullet.com/v2/pushes",
    }
    task_list = []  # empty list

    with caplog.at_level("INFO"), patch(
        "homeassistant.components.google_tasks.notifications_push.ClientSession"
    ) as Session:
        await send_pushbullet_notification(config_entry, task_list)

        # No HTTP session should be created
        Session.assert_not_called()

        # Optional: confirm the informational log was emitted
        assert any(
            "No tasks to notify; skipping Pushbullet notification" in r.message
            for r in caplog.records
        )
