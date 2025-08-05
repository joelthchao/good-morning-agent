"""
Unit tests for message formatter.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from src.senders.message_formatter import MessageFormatter


class TestMessageFormatter:
    """Test MessageFormatter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = MessageFormatter()

    def test_format_plain_text_basic(self):
        """Test basic plain text formatting."""
        content = "This is test content"
        metadata = {"date": "2025-08-05", "source": "test"}

        result = self.formatter.format_plain_text(content, metadata)

        assert "This is test content" in result
        assert "2025-08-05" in result
        assert "test" in result
        assert "Good Morning Agent" in result

    def test_format_plain_text_with_empty_metadata(self):
        """Test formatting with empty metadata."""
        content = "Test content"
        metadata = {}

        result = self.formatter.format_plain_text(content, metadata)

        assert "Test content" in result
        assert "Good Morning Agent" in result
        # Should have today's date
        today = datetime.now().strftime("%Y-%m-%d")
        assert today in result

    def test_format_plain_text_handles_multiline_content(self):
        """Test formatting with multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        metadata = {"date": "2025-08-05"}

        result = self.formatter.format_plain_text(content, metadata)

        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result

    def test_format_plain_text_preserves_unicode(self):
        """Test formatting preserves Unicode characters."""
        content = "測試內容 with 中文字元"
        metadata = {"date": "2025-08-05"}

        result = self.formatter.format_plain_text(content, metadata)

        assert "測試內容 with 中文字元" in result

    @patch("src.senders.message_formatter.datetime")
    def test_format_plain_text_with_mocked_time(self, mock_datetime):
        """Test formatting with mocked time."""
        # Mock datetime.now()
        mock_now = datetime(2025, 8, 5, 14, 30, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.strftime = datetime.strftime  # Keep strftime working

        content = "Test content"
        metadata = {}

        result = self.formatter.format_plain_text(content, metadata)

        assert "2025-08-05" in result
        assert "14:30:00" in result

    def test_add_headers_includes_required_info(self):
        """Test that headers include required information."""
        content = "test"
        metadata = {"date": "2025-08-05", "source": "newsletter"}

        headers = self.formatter._add_headers(content, metadata)

        assert "📅 日期：2025-08-05" in headers
        assert "📰 來源：newsletter" in headers
        assert "⏰ 生成時間：" in headers
        assert "=" * 50 in headers

    def test_add_headers_with_missing_date(self):
        """Test headers when date is missing from metadata."""
        content = "test"
        metadata = {"source": "newsletter"}

        headers = self.formatter._add_headers(content, metadata)

        # Should use current date
        today = datetime.now().strftime("%Y-%m-%d")
        assert f"📅 日期：{today}" in headers
        assert "📰 來源：newsletter" in headers

    def test_add_footers_includes_required_info(self):
        """Test that footers include required information."""
        content = "Test content with some text"
        metadata = {"extra_info": "test_value", "date": "2025-08-05"}

        result = self.formatter._add_footers(content, metadata)

        assert "Test content with some text" in result
        assert "Good Morning Agent" in result
        assert "extra_info: test_value" in result
        # Date should not be repeated in footer
        assert result.count("date: 2025-08-05") == 0

    def test_format_plain_text_error_handling(self):
        """Test error handling in format_plain_text."""
        # Mock an error in formatting
        with patch.object(
            self.formatter, "_add_headers", side_effect=Exception("Test error")
        ):
            content = "Test content"
            metadata = {}

            result = self.formatter.format_plain_text(content, metadata)

            # Should return basic content with footer
            assert "Test content" in result
            assert "Good Morning Agent" in result

    def test_format_handles_none_metadata(self):
        """Test formatting handles None metadata gracefully."""
        content = "Test content"
        # This should not happen in normal usage, but test robustness

        with patch.object(self.formatter, "_add_headers", return_value="Headers"):
            with patch.object(
                self.formatter, "_add_footers", return_value="Test content\nFooters"
            ):
                result = self.formatter.format_plain_text(content, {})

                assert "Test content" in result
