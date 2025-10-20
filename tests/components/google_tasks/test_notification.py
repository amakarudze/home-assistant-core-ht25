"""Tests for Google Tasks notification functionality."""

import smtplib
from unittest.mock import AsyncMock, Mock, patch

import pytest

from homeassistant.components.google_tasks.exceptions import GoogleTaskNotificationError
from homeassistant.components.google_tasks.notifications_email import (
    async_send_email_notification,
)
from homeassistant.components.google_tasks.notifications_push import (
    async_send_pushbullet_notification,
)


class TestEmailNotification:
    """Test email notification functionality."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        return Mock()

    @pytest.fixture
    def mock_config_entry(self):
        """Create a mock config entry with email options."""
        config_entry = Mock()
        config_entry.options = {
            "smtp_username": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "smtp_password": "password123",
            "smtp_host": "smtp.gmail.com",
            "smtp_port": "587",
        }
        return config_entry

    @pytest.mark.asyncio
    async def test_send_email_notification_success(self, mock_hass, mock_config_entry):
        """Test successful email sending."""
        task_list = ["Task 1", "Task 2", "Task 3"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server

            await async_send_email_notification(mock_hass, mock_config_entry, task_list)

            # Verify SMTP calls
            mock_smtp.assert_called_once_with("smtp.gmail.com", 587, timeout=30)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with(
                "sender@example.com", "password123"
            )
            mock_server.sendmail.assert_called_once()
            mock_server.quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_notification_with_defaults(self, mock_hass):
        """Test email sending with default SMTP settings."""
        task_list = ["Task 1"]
        config_entry = Mock()
        config_entry.options = {
            "smtp_username": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "smtp_password": "password123",
            # No smtp_host or smtp_port - should use defaults
        }

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server

            await async_send_email_notification(mock_hass, config_entry, task_list)

            # Should use default port 587, empty host
            mock_smtp.assert_called_once_with("", 587, timeout=30)

    @pytest.mark.asyncio
    async def test_empty_task_list_skips_email(self, mock_hass, mock_config_entry):
        """Test that empty task list skips email sending."""
        task_list = []

        with patch("smtplib.SMTP") as mock_smtp:
            result = await async_send_email_notification(
                mock_hass, mock_config_entry, task_list
            )

            # Should return None and not create SMTP connection
            assert result is None
            mock_smtp.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_required_fields_raises_error(self, mock_hass):
        """Test that missing required fields raise error."""
        task_list = ["Task 1"]
        config_entry = Mock()
        config_entry.options = {
            "smtp_username": "sender@example.com",
            # Missing recipient_email and smtp_password
        }

        with pytest.raises(
            GoogleTaskNotificationError,
            match="Missing required email configuration fields",
        ):
            await async_send_email_notification(mock_hass, config_entry, task_list)

    @pytest.mark.asyncio
    async def test_invalid_port_raises_error(self, mock_hass):
        """Test that invalid port raises error."""
        task_list = ["Task 1"]
        config_entry = Mock()
        config_entry.options = {
            "smtp_username": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "smtp_password": "password123",
            "smtp_port": "invalid_port",
        }

        with pytest.raises(GoogleTaskNotificationError, match="Invalid port number"):
            await async_send_email_notification(mock_hass, config_entry, task_list)

    @pytest.mark.asyncio
    async def test_smtp_authentication_error(self, mock_hass, mock_config_entry):
        """Test SMTP authentication error handling."""
        task_list = ["Task 1"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
                535, "Authentication failed"
            )

            with pytest.raises(
                GoogleTaskNotificationError, match="Authentication failed"
            ):
                await async_send_email_notification(
                    mock_hass, mock_config_entry, task_list
                )

    @pytest.mark.asyncio
    async def test_smtp_recipients_refused_error(self, mock_hass, mock_config_entry):
        """Test SMTP recipients refused error handling."""
        task_list = ["Task 1"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.sendmail.side_effect = smtplib.SMTPRecipientsRefused({})

            with pytest.raises(
                GoogleTaskNotificationError, match="Recipient email address refused"
            ):
                await async_send_email_notification(
                    mock_hass, mock_config_entry, task_list
                )

    @pytest.mark.asyncio
    async def test_smtp_sender_refused_error(self, mock_hass, mock_config_entry):
        """Test SMTP sender refused error handling."""
        task_list = ["Task 1"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.sendmail.side_effect = smtplib.SMTPSenderRefused(
                550, "Sender refused", "sender@example.com"
            )

            with pytest.raises(
                GoogleTaskNotificationError, match="Sender email address refused"
            ):
                await async_send_email_notification(
                    mock_hass, mock_config_entry, task_list
                )

    @pytest.mark.asyncio
    async def test_smtp_timeout_error(self, mock_hass, mock_config_entry):
        """Test SMTP timeout error handling."""
        task_list = ["Task 1"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = TimeoutError("Connection timed out")

            with pytest.raises(
                GoogleTaskNotificationError, match="SMTP connection timed out"
            ):
                await async_send_email_notification(
                    mock_hass, mock_config_entry, task_list
                )

    @pytest.mark.asyncio
    async def test_smtp_general_error(self, mock_hass, mock_config_entry):
        """Test general SMTP error handling."""
        task_list = ["Task 1"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.sendmail.side_effect = smtplib.SMTPException(
                "General SMTP error"
            )

            with pytest.raises(
                GoogleTaskNotificationError, match="Failed to send email notification"
            ):
                await async_send_email_notification(
                    mock_hass, mock_config_entry, task_list
                )

    @pytest.mark.asyncio
    async def test_server_quit_error_handled_gracefully(
        self, mock_hass, mock_config_entry
    ):
        """Test that server.quit() errors are handled gracefully."""
        task_list = ["Task 1"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.quit.side_effect = smtplib.SMTPException(
                "Error closing connection"
            )

            # Should not raise exception despite quit() error
            await async_send_email_notification(mock_hass, mock_config_entry, task_list)

            mock_server.quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_content_format(self, mock_hass, mock_config_entry):
        """Test that email content is formatted correctly."""
        task_list = ["Buy groceries", "Walk the dog", "Finish project"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server

            await async_send_email_notification(mock_hass, mock_config_entry, task_list)

            # Check that sendmail was called with correct parameters
            call_args = mock_server.sendmail.call_args[0]
            assert call_args[0] == "sender@example.com"
            assert call_args[1] == "recipient@example.com"

            # Check email content contains tasks
            email_content = call_args[2]
            assert "You are pending with 3 task(s)" in email_content
            assert "- Buy groceries" in email_content
            assert "- Walk the dog" in email_content
            assert "- Finish project" in email_content
            assert "Subject: Daily reminder" in email_content


class TestPushNotification:
    """Test push notification functionality."""

    @pytest.fixture
    def mock_hass(self):
        """Create a mock Home Assistant instance."""
        return Mock()

    @pytest.fixture
    def mock_config_entry(self):
        """Create a mock config entry with push options."""
        config_entry = Mock()
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
        config_entry = Mock()
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
