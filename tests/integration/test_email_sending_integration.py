"""
Integration tests for email sending functionality.

These tests use mocked SMTP servers to test the full email sending pipeline
without actually sending emails.
"""

import logging
from unittest.mock import Mock, patch

import pytest

from src.senders import EmailData, EmailSender, SendResult
from src.utils.config import EmailConfig


@pytest.fixture
def mock_email_config():
    """Create a mock email configuration for testing."""
    config = Mock(spec=EmailConfig)
    config.smtp_server = "smtp.gmail.com"
    config.smtp_port = 587
    config.sender_email = "test-sender@example.com"
    config.sender_password = "test-sender-password"
    config.address = "test-main@example.com"
    config.password = "test-main-password"
    return config


@pytest.fixture
def sample_email_data():
    """Create sample email data for testing."""
    return EmailData(
        recipient="recipient@example.com",
        subject="Integration Test Email",
        content="""這是一個整合測試郵件。

內容包含：
- 多行文字
- 中文字元
- 特殊符號 !@#$%^&*()

請忽略此測試郵件。""",
        metadata={
            "date": "2025-08-05",
            "source": "integration_test",
            "test_id": "test_001",
        },
    )


class TestEmailSendingIntegration:
    """Integration tests for the complete email sending pipeline."""

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_full_email_sending_pipeline(
        self, mock_smtp, mock_email_config, sample_email_data
    ):
        """Test the complete email sending pipeline with mocked SMTP."""
        # Setup mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Create email sender
        sender = EmailSender(mock_email_config)

        # Send email
        result = sender.send_email(sample_email_data)

        # Verify success
        assert result.success is True
        assert result.message_id is not None
        assert result.retry_count == 0
        assert result.error_message is None

        # Verify SMTP interactions
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with(
            "test-sender@example.com", "test-sender-password"
        )
        mock_server.send_message.assert_called_once()

        # Verify message content was processed
        call_args = mock_server.send_message.call_args[0][0]
        assert call_args["To"] == "recipient@example.com"
        assert call_args["Subject"].startswith(
            "Integration Test Email"
        )  # May have anti-spam suffix
        assert call_args["From"] == "test-sender@example.com"

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_email_formatting_integration(
        self, mock_smtp, mock_email_config, sample_email_data
    ):
        """Test that email formatting works correctly in integration."""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Capture the formatted message
        captured_message = None

        def capture_message(msg):
            nonlocal captured_message
            captured_message = msg

        mock_server.send_message.side_effect = capture_message

        sender = EmailSender(mock_email_config)
        result = sender.send_email(sample_email_data)

        assert result.success is True
        assert captured_message is not None

        # Extract the text payload and decode if needed
        text_part = captured_message.get_payload()[0]
        formatted_message = text_part.get_payload(decode=True).decode("utf-8")

        # Verify formatted content contains expected elements
        assert "這是一個整合測試郵件" in formatted_message
        assert "📅 日期：2025-08-05" in formatted_message
        assert "📰 來源：integration_test" in formatted_message
        assert "Good Morning Agent" in formatted_message
        assert "test_id: test_001" in formatted_message

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_security_measures_integration(
        self, mock_smtp, mock_email_config, sample_email_data
    ):
        """Test that security measures are applied in integration."""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = EmailSender(mock_email_config)
        result = sender.send_email(sample_email_data)

        assert result.success is True

        # Verify security headers were added
        call_args = mock_server.send_message.call_args[0][0]
        assert call_args["X-Mailer"] is not None
        assert "Good Morning Agent" in call_args["X-Mailer"]
        assert call_args["Message-ID"] is not None
        assert call_args["X-Priority"] == "3 (Normal)"

    @patch.dict("os.environ", {"EMAIL_SEND_INTERVAL": "1"})
    @patch("src.senders.email_sender.smtplib.SMTP")
    @patch("time.sleep")
    def test_rate_limiting_integration(
        self, mock_sleep, mock_smtp, mock_email_config, sample_email_data
    ):
        """Test rate limiting works in integration."""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = EmailSender(mock_email_config)

        # Send first email
        result1 = sender.send_email(sample_email_data)
        assert result1.success is True

        # Send second email immediately - should trigger rate limiting
        result2 = sender.send_email(sample_email_data)
        assert result2.success is True

        # Should have called sleep for rate limiting
        mock_sleep.assert_called()

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_retry_mechanism_integration(
        self, mock_smtp, mock_email_config, sample_email_data
    ):
        """Test retry mechanism works in integration."""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Fail first two attempts, succeed on third
        mock_server.send_message.side_effect = [
            Exception("Temporary error 1"),
            Exception("Temporary error 2"),
            None,  # Success
        ]

        sender = EmailSender(mock_email_config)

        with patch("time.sleep"):  # Speed up test
            result = sender.send_email(sample_email_data)

        assert result.success is True
        assert result.retry_count == 2
        assert mock_server.send_message.call_count == 3

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_connection_validation_integration(self, mock_smtp, mock_email_config):
        """Test connection validation in integration."""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = EmailSender(mock_email_config)

        # Test successful validation
        result = sender.validate_connection()
        assert result is True

        mock_server.starttls.assert_called()
        mock_server.login.assert_called_with(
            "test-sender@example.com", "test-sender-password"
        )

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_error_handling_integration(
        self, mock_smtp, mock_email_config, sample_email_data
    ):
        """Test error handling in integration."""
        # Test SMTP connection failure
        mock_smtp.side_effect = Exception("Connection failed")

        sender = EmailSender(mock_email_config)
        result = sender.send_email(sample_email_data)

        assert result.success is False
        assert "Connection failed" in result.error_message
        assert result.retry_count > 0  # Should have attempted retries

    def test_config_validation_integration(self, mock_email_config):
        """Test configuration validation in integration."""
        # Test with invalid config
        mock_email_config.smtp_server = None

        from src.senders.email_sender import EmailSenderError

        with pytest.raises(EmailSenderError):
            EmailSender(mock_email_config)

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_multiple_emails_integration(self, mock_smtp, mock_email_config):
        """Test sending multiple emails in sequence."""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        sender = EmailSender(mock_email_config)

        # Send multiple emails
        emails = [
            EmailData(
                recipient=f"user{i}@example.com",
                subject=f"Test Email {i}",
                content=f"Content for email {i}",
                metadata={"email_number": i},
            )
            for i in range(3)
        ]

        results = []
        with patch("time.sleep"):  # Speed up rate limiting
            for email in emails:
                result = sender.send_email(email)
                results.append(result)

        # All should succeed
        for result in results:
            assert result.success is True
            assert result.message_id is not None

        # Should have sent all emails
        assert mock_server.send_message.call_count == 3

    @patch("src.senders.email_sender.smtplib.SMTP")
    def test_unicode_content_integration(self, mock_smtp, mock_email_config):
        """Test handling of Unicode content in integration."""
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        # Email with various Unicode characters
        unicode_email = EmailData(
            recipient="test@example.com",
            subject="Unicode Test 測試 🚀",
            content="""
            多語言測試內容：

            中文：你好世界
            日文：こんにちは世界
            韓文：안녕하세요 세계
            Emoji: 🌍🚀📧✨

            特殊字符：©®™€£¥§
            """,
            metadata={"type": "unicode_test"},
        )

        sender = EmailSender(mock_email_config)
        result = sender.send_email(unicode_email)

        assert result.success is True

        # Verify the message was sent
        mock_server.send_message.assert_called_once()

        # Verify subject contains Unicode
        call_args = mock_server.send_message.call_args[0][0]
        assert "測試" in call_args["Subject"]
