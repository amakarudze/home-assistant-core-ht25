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

<<<<<<< HEAD
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
    async def test_send_email_notification_success(self,  mock_config_entry):
        """Test successful email sending."""
        task_list = ["Task 1", "Task 2", "Task 3"]
=======
    def test_send_email_notification_success(self):
        """Test successful email sending."""
        task_list = ["Task 1", "Task 2", "Task 3"]
        email_config = {
            "sender_email": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "sender_password": "password123",
            "host_name": "smtp.gmail.com",
            "port": "587",
        }
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server

<<<<<<< HEAD
            send_email_notification(mock_config_entry, task_list)
=======
            send_email_notification(task_list, email_config)
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)

            # Verify SMTP calls
            mock_smtp.assert_called_once_with("smtp.gmail.com", 587, timeout=30)
            mock_server.starttls.assert_called_once()
            mock_server.login.assert_called_once_with(
                "sender@example.com", "password123"
            )
            mock_server.sendmail.assert_called_once()
            mock_server.quit.assert_called_once()

<<<<<<< HEAD
    @pytest.mark.asyncio
    async def test_send_email_notification_with_defaults(self):
        """Test email sending with default SMTP settings."""
        task_list = ["Task 1"]
        config_entry = Mock()
        config_entry.options = {
            "smtp_username": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "smtp_password": "password123",
            # No smtp_host or smtp_port - should use defaults (empty host, 587)
=======
    def test_send_email_notification_with_defaults(self):
        """Test email sending with default SMTP settings."""
        task_list = ["Task 1"]
        email_config = {
            "sender_email": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "sender_password": "password123",
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)
        }

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server

<<<<<<< HEAD
            send_email_notification(config_entry, task_list)

            # Should use default port 587, empty host
            mock_smtp.assert_called_once_with("", 587, timeout=30)

    @pytest.mark.asyncio
    async def test_empty_task_list_skips_email(self,  mock_config_entry):
        """Test that empty task list skips email sending."""
        task_list = []

        with patch("smtplib.SMTP") as mock_smtp:
            send_email_notification(mock_config_entry, task_list)

            # Should return None and not create SMTP connection
            mock_smtp.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_required_fields_raises_error(self):
        """Negative: missing required fields -> error; SMTP must NOT be called."""
        task_list = ["Task 1"]
        config_entry = Mock()
        config_entry.options = {
            "smtp_username": "sender@example.com",
            # Missing recipient_email and smtp_password
        }

        with patch("smtplib.SMTP") as smtp_mock:
            with pytest.raises(
                GoogleTaskNotificationError,
                match="Missing required email configuration fields",
            ):
                send_email_notification( config_entry, task_list)
            # Negative expectation: no SMTP connection attempted
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
            send_email_notification( config_entry, task_list)

    @pytest.mark.asyncio
    async def test_smtp_authentication_error(self,  mock_config_entry):
        """Test SMTP authentication error handling."""
        task_list = ["Task 1"]
=======
            send_email_notification(task_list, email_config)

            # Should use default host and port
            mock_smtp.assert_called_once_with("smtp.gmail.com", 587, timeout=30)

    def test_empty_task_list_skips_email(self):
        """Test that empty task list skips email sending."""
        task_list = []
        email_config = {
            "sender_email": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "sender_password": "password123",
        }

        with patch("smtplib.SMTP") as mock_smtp:
            send_email_notification(task_list, email_config)

            # Should not create SMTP connection
            mock_smtp.assert_not_called()

    def test_missing_email_config_raises_error(self):
        """Test that missing email config raises error."""
        task_list = ["Task 1"]

        with pytest.raises(
            GoogleTaskNotificationError, match="Email configuration is missing"
        ):
            send_email_notification(task_list, {})

    def test_missing_required_fields_raises_error(self):
        """Test that missing required fields raise error."""
        task_list = ["Task 1"]
        email_config = {
            "sender_email": "sender@example.com",
            # Missing recipient_email and sender_password
        }

        with pytest.raises(
            GoogleTaskNotificationError,
            match="Missing required email configuration fields",
        ):
            send_email_notification(task_list, email_config)

    def test_invalid_port_raises_error(self):
        """Test that invalid port raises error."""
        task_list = ["Task 1"]
        email_config = {
            "sender_email": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "sender_password": "password123",
            "port": "invalid_port",
        }

        with pytest.raises(GoogleTaskNotificationError, match="Invalid port number"):
            send_email_notification(task_list, email_config)

    def test_smtp_authentication_error(self):
        """Test SMTP authentication error handling."""
        task_list = ["Task 1"]
        email_config = {
            "sender_email": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "sender_password": "wrong_password",
        }
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)

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
        """Test SMTP recipients refused error handling."""
        task_list = ["Task 1"]
=======
                send_email_notification(task_list, email_config)

    def test_smtp_recipients_refused_error(self):
        """Test SMTP recipients refused error handling."""
        task_list = ["Task 1"]
        email_config = {
            "sender_email": "sender@example.com",
            "recipient_email": "invalid@example.com",
            "sender_password": "password123",
        }
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)

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
        """Test SMTP sender refused error handling."""
        task_list = ["Task 1"]
=======
                send_email_notification(task_list, email_config)

    def test_smtp_sender_refused_error(self):
        """Test SMTP sender refused error handling."""
        task_list = ["Task 1"]
        email_config = {
            "sender_email": "invalid@example.com",
            "recipient_email": "recipient@example.com",
            "sender_password": "password123",
        }
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server
            mock_server.sendmail.side_effect = smtplib.SMTPSenderRefused(
<<<<<<< HEAD
                550, "Sender refused", "sender@example.com"
=======
                550, "Sender refused", "invalid@example.com"
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)
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
        """Test SMTP timeout error handling."""
        task_list = ["Task 1"]
=======
                send_email_notification(task_list, email_config)

    def test_smtp_timeout_error(self):
        """Test SMTP timeout error handling."""
        task_list = ["Task 1"]
        email_config = {
            "sender_email": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "sender_password": "password123",
        }
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)

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
        """Test general SMTP error handling."""
        task_list = ["Task 1"]
=======
                send_email_notification(task_list, email_config)

    def test_smtp_general_error(self):
        """Test general SMTP error handling."""
        task_list = ["Task 1"]
        email_config = {
            "sender_email": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "sender_password": "password123",
        }
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)

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
        """Test that server.quit() errors are handled gracefully."""
        task_list = ["Task 1"]
=======
                send_email_notification(task_list, email_config)

    def test_server_quit_error_handled_gracefully(self):
        """Test that server.quit() errors are handled gracefully."""
        task_list = ["Task 1"]
        email_config = {
            "sender_email": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "sender_password": "password123",
        }
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)

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
        """Test that email content is formatted correctly."""
        task_list = ["Buy groceries", "Walk the dog", "Finish project"]
=======
            # Should not raise exception despite quit() error
            send_email_notification(task_list, email_config)

            mock_server.quit.assert_called_once()

    def test_email_content_format(self):
        """Test that email content is formatted correctly."""
        task_list = ["Buy groceries", "Walk the dog", "Finish project"]
        email_config = {
            "sender_email": "sender@example.com",
            "recipient_email": "recipient@example.com",
            "sender_password": "password123",
        }
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)

        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = Mock()
            mock_smtp.return_value = mock_server

<<<<<<< HEAD
            send_email_notification( mock_config_entry, task_list)
=======
            send_email_notification(task_list, email_config)
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)

            # Check that sendmail was called with correct parameters
            call_args = mock_server.sendmail.call_args[0]
            assert call_args[0] == "sender@example.com"
            assert call_args[1] == "recipient@example.com"

<<<<<<< HEAD
            # Check email content contains tasks and subject
            email_content = call_args[2]
            assert "You are pending with 3 task(s)" in email_content
            assert "- Buy groceries" in email_content
            assert "- Walk the dog" in email_content
            assert "- Finish project" in email_content
            assert "Subject: Home Assistant - Daily Task Reminder" in email_content
=======
            # Check email content contains tasks
            email_content = call_args[2]
            assert "3 Google Tasks to-do item(s)" in email_content
            assert "- Buy groceries" in email_content
            assert "- Walk the dog" in email_content
            assert "- Finish project" in email_content
            assert "Subject: Daily reminder" in email_content
>>>>>>> 6e63f5eaef8 (Add email notification test for Google Tasks component)
