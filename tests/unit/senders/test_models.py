"""
Unit tests for email sender models.
"""

import pytest

from src.senders.models import EmailData, SendResult


class TestEmailData:
    """Test EmailData model."""

    def test_valid_email_data(self):
        """Test creating valid EmailData."""
        data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={"date": "2025-08-05"},
        )

        assert data.recipient == "test@example.com"
        assert data.subject == "Test Subject"
        assert data.content == "Test content"
        assert data.metadata["date"] == "2025-08-05"

    def test_empty_recipient_raises_error(self):
        """Test that empty recipient raises ValueError."""
        with pytest.raises(ValueError, match="Recipient is required"):
            EmailData(recipient="", subject="Test", content="Test", metadata={})

    def test_empty_subject_raises_error(self):
        """Test that empty subject raises ValueError."""
        with pytest.raises(ValueError, match="Subject is required"):
            EmailData(
                recipient="test@example.com", subject="", content="Test", metadata={}
            )

    def test_empty_content_raises_error(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="Content is required"):
            EmailData(
                recipient="test@example.com", subject="Test", content="", metadata={}
            )

    def test_invalid_email_address_raises_error(self):
        """Test that invalid email address raises ValueError."""
        with pytest.raises(ValueError, match="Recipient must be a valid email address"):
            EmailData(
                recipient="invalid-email", subject="Test", content="Test", metadata={}
            )


class TestSendResult:
    """Test SendResult model."""

    def test_successful_send_result(self):
        """Test creating successful SendResult."""
        result = SendResult(
            success=True, message_id="<test@example.com>", retry_count=1
        )

        assert result.success is True
        assert result.message_id == "<test@example.com>"
        assert result.error_message is None
        assert result.retry_count == 1

    def test_failed_send_result(self):
        """Test creating failed SendResult."""
        result = SendResult(success=False, error_message="SMTP error", retry_count=3)

        assert result.success is False
        assert result.message_id is None
        assert result.error_message == "SMTP error"
        assert result.retry_count == 3

    def test_successful_result_without_message_id_raises_error(self):
        """Test that successful result without message_id raises ValueError."""
        with pytest.raises(ValueError, match="Successful send must have a message_id"):
            SendResult(success=True)

    def test_failed_result_without_error_message_raises_error(self):
        """Test that failed result without error_message raises ValueError."""
        with pytest.raises(ValueError, match="Failed send must have an error_message"):
            SendResult(success=False)
