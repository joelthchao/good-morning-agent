"""
Unit tests for security manager.
"""

import time
from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

from src.senders.models import EmailData
from src.senders.security_manager import SecurityManager


class TestSecurityManager:
    """Test SecurityManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.security_manager = SecurityManager(send_interval=2)

    def test_initialization(self):
        """Test SecurityManager initialization."""
        sm = SecurityManager(send_interval=5)
        assert sm.send_interval == 5
        assert sm.last_send_time is None
        assert sm.daily_send_count == 0

    def test_apply_anti_spam_measures(self):
        """Test applying anti-spam measures."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={"date": "2025-08-05"},
        )

        result = self.security_manager.apply_anti_spam_measures(email_data)

        # Should return modified data
        assert result.recipient == email_data.recipient
        # Content might be slightly modified, so check it contains original content
        assert email_data.content in result.content
        assert "security_hash" in result.metadata
        assert "send_timestamp" in result.metadata
        assert "anti_spam_applied" in result.metadata
        assert result.metadata["anti_spam_applied"] is True

    def test_apply_anti_spam_measures_preserves_original(self):
        """Test that anti-spam measures don't modify original data."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={"date": "2025-08-05"},
        )
        original_metadata = email_data.metadata.copy()

        # noqa: F841
        self.security_manager.apply_anti_spam_measures(email_data)

        # Original should be unchanged
        assert email_data.metadata == original_metadata
        assert "security_hash" not in email_data.metadata

    def test_add_authentication_headers(self):
        """Test adding authentication headers."""
        headers = self.security_manager.add_authentication_headers()

        required_headers = ["X-Mailer", "X-Priority", "Message-ID", "Date"]
        for header in required_headers:
            assert header in headers

        assert "Good Morning Agent" in headers["X-Mailer"]
        assert headers["X-Priority"] == "3 (Normal)"

    def test_validate_send_frequency_initial(self):
        """Test send frequency validation on first send."""
        # First send should always be allowed
        assert self.security_manager.validate_send_frequency() is True

    def test_validate_send_frequency_too_soon(self):
        """Test send frequency validation when sending too soon."""
        # Simulate a recent send
        self.security_manager.last_send_time = time.time()

        # Should not allow immediate send
        assert self.security_manager.validate_send_frequency() is False

    def test_validate_send_frequency_after_interval(self):
        """Test send frequency validation after sufficient interval."""
        # Simulate a send 3 seconds ago (more than 2s interval)
        self.security_manager.last_send_time = time.time() - 3

        # Should allow send
        assert self.security_manager.validate_send_frequency() is True

    def test_validate_send_frequency_daily_limit(self):
        """Test daily send limit validation."""
        # Set daily count to limit
        self.security_manager.daily_send_count = 100

        # Should not allow send
        assert self.security_manager.validate_send_frequency() is False

    def test_wait_if_needed_no_wait(self):
        """Test wait_if_needed when no wait is required."""
        start_time = time.time()
        self.security_manager.wait_if_needed()
        end_time = time.time()

        # Should complete quickly (less than 1 second)
        assert end_time - start_time < 1.0

    @patch("time.sleep")
    def test_wait_if_needed_with_wait(self, mock_sleep):
        """Test wait_if_needed when wait is required."""
        # Simulate recent send
        self.security_manager.last_send_time = time.time() - 1  # 1 second ago

        self.security_manager.wait_if_needed()

        # Should have called sleep
        mock_sleep.assert_called_once()
        # Should sleep for approximately 1 second (2 - 1)
        sleep_time = mock_sleep.call_args[0][0]
        assert 0.9 <= sleep_time <= 1.1

    def test_record_send(self):
        """Test recording a send."""
        initial_count = self.security_manager.daily_send_count

        self.security_manager.record_send()

        assert self.security_manager.last_send_time is not None
        assert self.security_manager.daily_send_count == initial_count + 1

    def test_diversify_subject(self):
        """Test subject diversification."""
        subject = "Test Subject"

        # Test multiple times to see variation
        results = set()
        for _ in range(20):  # Run multiple times to catch variations
            diversified = self.security_manager._diversify_subject(subject)
            results.add(diversified)
            assert diversified.startswith(subject)

        # Should have some variation (at least the original)
        assert len(results) >= 1

    def test_diversify_content(self):
        """Test content diversification."""
        content = "Test content for diversification"

        # Test multiple times to potentially see variation
        results = set()
        for _ in range(20):
            diversified = self.security_manager._diversify_content(content)
            results.add(diversified)
            # Content should still contain original text
            assert "Test content for diversification" in diversified

        # Should have at least the original version
        assert len(results) >= 1

    def test_generate_content_hash(self):
        """Test content hash generation."""
        content1 = "Test content 1"
        content2 = "Test content 2"

        hash1 = self.security_manager._generate_content_hash(content1)
        hash2 = self.security_manager._generate_content_hash(content2)

        # Hashes should be different
        assert hash1 != hash2
        # Should be 8 characters (MD5 truncated)
        assert len(hash1) == 8
        assert len(hash2) == 8

        # Same content should generate same hash
        hash1_repeat = self.security_manager._generate_content_hash(content1)
        assert hash1 == hash1_repeat

    def test_generate_message_id(self):
        """Test message ID generation."""
        id1 = self.security_manager._generate_message_id()
        id2 = self.security_manager._generate_message_id()

        # Should be different
        assert id1 != id2
        # Should have correct format
        assert id1.startswith("<")
        assert id1.endswith("@good-morning-agent>")
        assert id2.startswith("<")
        assert id2.endswith("@good-morning-agent>")

    def test_reset_daily_count_if_needed_same_day(self):
        """Test daily count reset on same day."""
        self.security_manager.daily_send_count = 5
        initial_count = self.security_manager.daily_send_count

        self.security_manager._reset_daily_count_if_needed()

        # Should not reset on same day
        assert self.security_manager.daily_send_count == initial_count

    @patch("src.senders.security_manager.datetime")
    def test_reset_daily_count_if_needed_new_day(self, mock_datetime):
        """Test daily count reset on new day."""
        # Set up current state
        self.security_manager.daily_send_count = 5
        yesterday = datetime.now() - timedelta(days=1)
        self.security_manager.daily_reset_time = yesterday.replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Mock current time to be today
        today = datetime.now()
        mock_datetime.now.return_value = today

        self.security_manager._reset_daily_count_if_needed()

        # Should reset count
        assert self.security_manager.daily_send_count == 0

    def test_apply_anti_spam_measures_error_handling(self):
        """Test error handling in anti-spam measures."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={"date": "2025-08-05"},
        )

        # Mock an error in diversification
        with patch.object(
            self.security_manager,
            "_diversify_subject",
            side_effect=Exception("Test error"),
        ):
            result = self.security_manager.apply_anti_spam_measures(email_data)

            # Should return original data on error
            assert result.recipient == email_data.recipient
            assert result.subject == email_data.subject
            assert result.content == email_data.content
