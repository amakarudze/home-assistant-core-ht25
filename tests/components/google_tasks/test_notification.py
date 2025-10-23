"""Tests for Google Tasks email notification functionality."""

import smtplib
from unittest.mock import Mock, patch

import pytest

from homeassistant.components.google_tasks.exceptions import GoogleTaskNotificationError
from homeassistant.components.google_tasks.notifications_email import (
    send_email_notification,
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
<<<<<<< HEAD
    async def test_send_email_notification_success(self,  mock_config_entry):
=======
    async def test_send_email_notification_success(self, mock_config_entry):
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
        """Test successful email sending."""
        task_list = ["Task 1", "Task 2", "Task 3"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server

            send_email_notification(mock_config_entry, task_list)

            mock_smtp.assert_called_once_with("smtp.gmail.com", 587, timeout=30)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with(
                "sender@example.com", "password123"
            )
            mock_server.sendmail.assert_called_once()
            mock_server.quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_notification_with_defaults(self):
        """Test email sending with default SMTP settings."""
        task_list = ["Task 1"]
        config_entry = Mock()
        config_entry.options = {
            "smtp_username": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "smtp_password": "password123",
<<<<<<< HEAD
            # No smtp_host or smtp_port - should use defaults (empty host, 587)
=======
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
        }

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server

            send_email_notification(config_entry, task_list)

            mock_smtp.assert_called_once_with("", 587, timeout=30)

    @pytest.mark.asyncio
<<<<<<< HEAD
    async def test_empty_task_list_skips_email(self,  mock_config_entry):
=======
    async def test_empty_task_list_skips_email(self, mock_config_entry):
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
        """Test that empty task list skips email sending."""
        task_list = []

        with patch("smtplib.SMTP") as mock_smtp:
            send_email_notification(mock_config_entry, task_list)

<<<<<<< HEAD
            # Should return None and not create SMTP connection
=======
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
            mock_smtp.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_required_fields_raises_error(self):
        """Negative: missing required fields -> error; SMTP must NOT be called."""
        task_list = ["Task 1"]
        config_entry = Mock()
        config_entry.options = {
            "smtp_username": "sender@example.com",
        }

        with patch("smtplib.SMTP") as smtp_mock:
            with pytest.raises(
                GoogleTaskNotificationError,
                match="Missing required email configuration fields",
            ):
<<<<<<< HEAD
                send_email_notification( config_entry, task_list)
            # Negative expectation: no SMTP connection attempted
=======
                send_email_notification(config_entry, task_list)

>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
            smtp_mock.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_port_raises_error(self):
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
<<<<<<< HEAD
            send_email_notification( config_entry, task_list)

    @pytest.mark.asyncio
    async def test_smtp_authentication_error(self,  mock_config_entry):
=======
            send_email_notification(config_entry, task_list)

    @pytest.mark.asyncio
    async def test_smtp_authentication_error(self, mock_config_entry):
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
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
<<<<<<< HEAD
                send_email_notification(
                     mock_config_entry, task_list
                )

    @pytest.mark.asyncio
    async def test_smtp_recipients_refused_error(self,  mock_config_entry):
=======
                send_email_notification(mock_config_entry, task_list)

    @pytest.mark.asyncio
    async def test_smtp_recipients_refused_error(self, mock_config_entry):
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
        """Test SMTP recipients refused error handling."""
        task_list = ["Task 1"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.sendmail.side_effect = smtplib.SMTPRecipientsRefused({})

            with pytest.raises(
                GoogleTaskNotificationError, match="Recipient email address refused"
            ):
<<<<<<< HEAD
                send_email_notification(
                     mock_config_entry, task_list
                )

    @pytest.mark.asyncio
    async def test_smtp_sender_refused_error(self,  mock_config_entry):
=======
                send_email_notification(mock_config_entry, task_list)

    @pytest.mark.asyncio
    async def test_smtp_sender_refused_error(self, mock_config_entry):
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
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
<<<<<<< HEAD
                send_email_notification(
                     mock_config_entry, task_list
                )

    @pytest.mark.asyncio
    async def test_smtp_timeout_error(self,  mock_config_entry):
=======
                send_email_notification(mock_config_entry, task_list)

    @pytest.mark.asyncio
    async def test_smtp_timeout_error(self, mock_config_entry):
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
        """Test SMTP timeout error handling."""
        task_list = ["Task 1"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_smtp.side_effect = TimeoutError("Connection timed out")

            with pytest.raises(
                GoogleTaskNotificationError, match="SMTP connection timed out"
            ):
<<<<<<< HEAD
                send_email_notification(
                     mock_config_entry, task_list
                )

    @pytest.mark.asyncio
    async def test_smtp_general_error(self,  mock_config_entry):
=======
                send_email_notification(mock_config_entry, task_list)

    @pytest.mark.asyncio
    async def test_smtp_general_error(self, mock_config_entry):
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
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
<<<<<<< HEAD
                send_email_notification(
                     mock_config_entry, task_list
                )

    @pytest.mark.asyncio
    async def test_server_quit_error_handled_gracefully(
        self,  mock_config_entry
    ):
=======
                send_email_notification(mock_config_entry, task_list)

    @pytest.mark.asyncio
    async def test_server_quit_error_handled_gracefully(self, mock_config_entry):
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
        """Test that server.quit() errors are handled gracefully."""
        task_list = ["Task 1"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.quit.side_effect = smtplib.SMTPException(
                "Error closing connection"
            )

<<<<<<< HEAD
            # Should not raise despite quit() error
            send_email_notification( mock_config_entry, task_list)
            mock_server.quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_content_format(self,  mock_config_entry):
=======
            send_email_notification(mock_config_entry, task_list)
            mock_server.quit.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_content_format(self, mock_config_entry):
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
        """Test that email content is formatted correctly."""
        task_list = ["Buy groceries", "Walk the dog", "Finish project"]

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server

<<<<<<< HEAD
            send_email_notification( mock_config_entry, task_list)
=======
            send_email_notification(mock_config_entry, task_list)
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d

            call_args = mock_server.sendmail.call_args[0]
            assert call_args[0] == "sender@example.com"
            assert call_args[1] == "recipient@example.com"

<<<<<<< HEAD
            # Check email content contains tasks and subject
=======
>>>>>>> 36d2a20e4625b8dcb44c5bdbdf76ff2f9e0b382d
            email_content = call_args[2]
            assert "You are pending with 3 task(s)" in email_content
            assert "- Buy groceries" in email_content
            assert "- Walk the dog" in email_content
            assert "- Finish project" in email_content
            assert "Subject: Home Assistant - Daily Task Reminder" in email_content
