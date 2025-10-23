import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from homeassistant.components.google_tasks.notifications_push import send_pushbullet_notification


def make_session_with_resp(resp):
    session = MagicMock()
    post_cm = MagicMock()
    post_cm.__aenter__ = AsyncMock(return_value=resp)
    post_cm.__aexit__ = AsyncMock(return_value=None)
    session.post = MagicMock(return_value=post_cm)
    return session


class TestPushNotification:
    @pytest.fixture
    def mock_config_entry(self):
        config_entry = MagicMock()
        config_entry.options = {
            "access_token": "test_token_123",
            "api_endpoint": "https://api.pushbullet.com/v2/pushes",
        }
        return config_entry

    # 1. Successful Pushbullet Notification (Happy Path)
    @pytest.mark.asyncio
    async def test_send_pushbullet_notification_success(self, mock_config_entry):
        task_list = ["Task 1", "Task 2"]
        with patch("homeassistant.components.google_tasks.notifications_push.ClientSession") as Session:
            resp = MagicMock()
            resp.status = 200
            session = make_session_with_resp(resp)
            Session.return_value.__aenter__.return_value = session
            await send_pushbullet_notification(mock_config_entry, task_list)
            assert session.post.call_count == 1

    # 2. Missing Access Token → Should Skip Immediately
    @pytest.mark.asyncio
    async def test_pushbullet_missing_access_token(self):
        task_list = ["Task 1"]
        config_entry = MagicMock()
        config_entry.options = {}
        with patch("homeassistant.components.google_tasks.notifications_push.ClientSession") as Session:
            await send_pushbullet_notification(config_entry, task_list)
            Session.assert_not_called()

    # 3. API Error (400 Bad Request) → Logs Error
    @pytest.mark.asyncio
    async def test_pushbullet_api_error(self, mock_config_entry, caplog):
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

    # 4. Network Error (e.g., Timeout) → Exception Caught
    @pytest.mark.asyncio
    async def test_pushbullet_network_error(self, mock_config_entry, caplog):
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


# 5. Validate Endpoint, Headers, and Payload Structure are All Correct
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


# 6. Handle Rate-Limited (429) Error → Log but Don’t Crash
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
        assert any(
            r.levelno == logging.ERROR
            and "Failed to send Pushbullet notification [429]: Too Many Requests" in r.message
            for r in caplog.records
        )


# 7. Empty Task List → Skip Notification and Log Info Message
@pytest.mark.asyncio
async def test_pushbullet_empty_task_list_skips_call(caplog):
    config_entry = MagicMock()
    config_entry.options = {
        "access_token": "tok123",
        "api_endpoint": "https://api.pushbullet.com/v2/pushes",
    }
    task_list = []
    with caplog.at_level("INFO"), patch(
        "homeassistant.components.google_tasks.notifications_push.ClientSession"
    ) as Session:
        await send_pushbullet_notification(config_entry, task_list)
        Session.assert_not_called()
        assert any(
            "No tasks to notify; skipping Pushbullet notification" in r.message
            for r in caplog.records
        )
