"""
Unit tests for email sender.
"""

import smtplib
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.senders.email_sender import EmailSender, EmailSenderError
from src.senders.models import EmailData, SendResult


class MockEmailConfig:
    """Mock email configuration for testing."""

    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "sender@example.com"
        self.sender_password = "sender_password"
        self.address = "main@example.com"
        self.password = "main_password"


class TestEmailSender:
    """Test EmailSender class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = MockEmailConfig()
        with patch.dict("os.environ", {"EMAIL_SEND_INTERVAL": "2"}):
            self.sender = EmailSender(self.config)

    def test_initialization(self):
        """Test EmailSender initialization."""
        assert self.sender.config == self.config
        assert self.sender.formatter is not None
        assert self.sender.security_manager is not None

    def test_initialization_missing_smtp_server(self):
        """Test initialization with missing SMTP server."""
        config = MockEmailConfig()
        config.smtp_server = None

        with pytest.raises(EmailSenderError, match="SMTP server is required"):
            EmailSender(config)

    def test_initialization_missing_sender_email(self):
        """Test initialization with missing sender email."""
        config = MockEmailConfig()
        config.sender_email = None
        config.address = None

        with pytest.raises(EmailSenderError, match="Sender email is required"):
            EmailSender(config)

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_validate_connection_success(self, mock_smtp):
        """Test successful connection validation."""
        # Mock successful SMTP connection
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = self.sender.validate_connection()

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(
            "sender@example.com", "sender_password"
        )

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_validate_connection_failure(self, mock_smtp):
        """Test connection validation failure."""
        # Mock SMTP connection failure
        mock_smtp.side_effect = smtplib.SMTPException("Connection failed")

        result = self.sender.validate_connection()

        assert result is False

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_validate_connection_uses_main_credentials_when_sender_missing(
        self, mock_smtp
    ):
        """Test connection validation uses main credentials when sender missing."""
        # Remove sender credentials
        config = MockEmailConfig()
        config.sender_email = None
        config.sender_password = None
        sender = EmailSender(config)

        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        result = sender.validate_connection()

        assert result is True
        mock_server.login.assert_called_once_with("main@example.com", "main_password")

    def test_send_email_missing_recipient(self):
        """Test send_email with missing recipient."""
        # This should raise during EmailData validation
        with pytest.raises(ValueError, match="Recipient is required"):
            EmailData(recipient="", subject="Test", content="Test", metadata={})

    @patch("src.senders.email_sender.EmailSender._retry_send")
    def test_send_email_success(self, mock_retry):
        """Test successful email sending."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={"date": "2025-08-05"},
        )

        # Mock successful send
        mock_retry.return_value = SendResult(
            success=True, message_id="<test@example.com>", retry_count=0
        )

        result = self.sender.send_email(email_data)

        assert result.success is True
        assert result.message_id == "<test@example.com>"
        mock_retry.assert_called_once()

    @patch("src.senders.email_sender.EmailSender._send_single_email")
    def test_retry_send_success_first_attempt(self, mock_send):
        """Test retry send succeeding on first attempt."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={},
        )

        mock_send.return_value = "<test@example.com>"

        result = self.sender._retry_send(email_data, max_retries=3)

        assert result.success is True
        assert result.message_id == "<test@example.com>"
        assert result.retry_count == 0
        mock_send.assert_called_once()

    @patch("src.senders.email_sender.EmailSender._send_single_email")
    @patch("time.sleep")  # Mock sleep to speed up test
    def test_retry_send_success_after_retries(self, mock_sleep, mock_send):
        """Test retry send succeeding after retries."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={},
        )

        # Fail twice, then succeed
        mock_send.side_effect = [
            Exception("Temporary error"),
            Exception("Another error"),
            "<test@example.com>",
        ]

        result = self.sender._retry_send(email_data, max_retries=3)

        assert result.success is True
        assert result.message_id == "<test@example.com>"
        assert result.retry_count == 2
        assert mock_send.call_count == 3

    @patch("src.senders.email_sender.EmailSender._send_single_email")
    @patch("time.sleep")
    def test_retry_send_all_attempts_fail(self, mock_sleep, mock_send):
        """Test retry send when all attempts fail."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={},
        )

        mock_send.side_effect = Exception("Persistent error")

        result = self.sender._retry_send(email_data, max_retries=2)

        assert result.success is False
        assert "Persistent error" in result.error_message
        assert result.retry_count == 3  # max_retries + 1
        assert mock_send.call_count == 3

    @patch("src.senders.email_sender.EmailSender._send_single_email")
    def test_retry_send_authentication_error_no_retry(self, mock_send):
        """Test retry send stops on authentication error."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={},
        )

        mock_send.side_effect = Exception("Authentication failed")

        result = self.sender._retry_send(email_data, max_retries=3)

        assert result.success is False
        assert "Authentication failed" in result.error_message
        # Should not retry on auth errors
        mock_send.assert_called_once()

    @patch("src.senders.email_sender.smtplib.SMTP")
    @patch("src.senders.email_sender.MIMEMultipart")
    @patch("src.senders.email_sender.MIMEText")
    def test_send_single_email_success(
        self, mock_mime_text, mock_mime_multipart, mock_smtp
    ):
        """Test successful single email send."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={"date": "2025-08-05"},
        )

        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Mock message creation to return a message ID
        mock_message = MagicMock()
        mock_message.get.return_value = "<test-message-id>"
        mock_message.__setitem__ = MagicMock()  # Allow item assignment
        mock_message.__getitem__ = MagicMock()  # Allow item access
        mock_mime_multipart.return_value = mock_message

        result = self.sender._send_single_email(email_data)

        assert result == "<test-message-id>"
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(
            "sender@example.com", "sender_password"
        )
        mock_server.send_message.assert_called_once()

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_send_single_email_smtp_auth_error(self, mock_smtp):
        """Test single email send with SMTP authentication error."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={},
        )

        mock_server = Mock()
        mock_server.login.side_effect = smtplib.SMTPAuthenticationError(
            535, "Authentication failed"
        )
        mock_smtp.return_value.__enter__.return_value = mock_server

        with pytest.raises(EmailSenderError, match="Authentication failed"):
            self.sender._send_single_email(email_data)

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_send_single_email_recipients_refused(self, mock_smtp):
        """Test single email send with recipients refused error."""
        email_data = EmailData(
            recipient="invalid@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={},
        )

        mock_server = Mock()
        mock_server.send_message.side_effect = smtplib.SMTPRecipientsRefused(
            {"invalid@example.com": (550, "No such user")}
        )
        mock_smtp.return_value.__enter__.return_value = mock_server

        with patch("src.senders.email_sender.MIMEMultipart"):
            with pytest.raises(EmailSenderError, match="Recipient refused"):
                self.sender._send_single_email(email_data)

    @patch("src.senders.email_sender.smtplib.SMTP")
    @patch("src.senders.email_sender.MIMEMultipart")
    @patch("src.senders.email_sender.MIMEText")
    def test_send_single_email_uses_main_credentials_when_needed(
        self, mock_mime_text, mock_mime_multipart, mock_smtp
    ):
        """Test single email send uses main credentials when sender credentials missing."""
        # Configure without sender credentials
        config = MockEmailConfig()
        config.sender_email = None
        config.sender_password = None
        sender = EmailSender(config)

        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={},
        )

        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        mock_message = MagicMock()
        mock_message.get.return_value = "<test-message-id>"
        mock_message.__setitem__ = MagicMock()  # Allow item assignment
        mock_message.__getitem__ = MagicMock()  # Allow item access
        mock_mime_multipart.return_value = mock_message

        sender._send_single_email(email_data)

        # Should use main credentials
        mock_server.login.assert_called_once_with("main@example.com", "main_password")

    def test_send_email_unexpected_error(self):
        """Test send_email handles unexpected errors."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={},
        )

        # Mock unexpected error in retry_send
        with patch.object(
            self.sender, "_retry_send", side_effect=Exception("Unexpected error")
        ):
            result = self.sender.send_email(email_data)

        assert result.success is False
        assert "Unexpected error" in result.error_message
        assert result.retry_count == 0
