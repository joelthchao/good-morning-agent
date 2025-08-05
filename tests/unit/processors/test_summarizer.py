"""
Unit tests for summarizer functionality.

Purpose: Verify 100-character truncation logic correctness,
especially for Unicode content and edge cases.
"""

import pytest

from src.processors.summarizer import Summarizer


class TestSummarizer:
    """Test Summarizer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.summarizer = Summarizer()

    def test_short_content_preserved_completely(self):
        """Purpose: Verify content shorter than 100 chars is preserved without truncation."""
        content = "This is a short newsletter content."

        result = self.summarizer.summarize(content)

        assert result == content
        assert len(result) == len(content)
        assert not result.endswith("...")

    def test_long_content_truncated_to_300_chars(self):
        """Purpose: Verify content longer than 300 chars is truncated correctly."""
        content = (
            "This is a very long newsletter content that definitely exceeds three hundred characters and should be truncated properly with ellipsis. "
            + "A" * 200
        )

        result = self.summarizer.summarize(content)

        assert len(result) <= 303  # max 300 chars + "..."
        assert result.endswith("...")
        # Should try to break at sentence boundary

    def test_exactly_300_chars_no_truncation(self):
        """Purpose: Verify boundary condition - exactly 300 chars needs no truncation."""
        content = "a" * 300  # Exactly 300 characters

        result = self.summarizer.summarize(content)

        assert result == content
        assert len(result) == 300
        assert not result.endswith("...")

    def test_exactly_301_chars_gets_truncated(self):
        """Purpose: Verify boundary condition - 301 chars gets truncated."""
        content = "a" * 301  # Exactly 301 characters

        result = self.summarizer.summarize(content)

        assert len(result) <= 303  # max 300 chars + "..."
        assert result.endswith("...")
        assert result.startswith(content[:200])  # Should start with original content

    def test_empty_content_returns_empty(self):
        """Purpose: Verify edge case - empty content handling."""
        content = ""

        result = self.summarizer.summarize(content)

        assert result == ""
        assert len(result) == 0

    def test_unicode_chinese_content_truncation(self):
        """Purpose: Verify Unicode (Chinese) content is truncated correctly without corruption."""
        content = "測試中文內容處理" * 50  # Creates long Chinese content

        result = self.summarizer.summarize(content)

        # Should be truncated
        assert len(result) <= 303  # max 300 chars + "..."
        assert result.endswith("...")

        # Should not have corrupted Unicode characters
        truncated_part = result[:-3]  # Remove "..."
        assert len(truncated_part) <= 300

        # Verify it's valid Unicode - should start with original content
        assert truncated_part.startswith(content[:100])

    def test_mixed_unicode_and_ascii_content(self):
        """Purpose: Verify mixed Unicode and ASCII content handling."""
        content = "Hello 世界 " * 40  # Mixed English and Chinese

        result = self.summarizer.summarize(content)

        assert len(result) <= 303  # max 300 chars + "..."
        assert result.endswith("...")
        assert result.startswith(content[:100])

    def test_content_with_emoji_truncation(self):
        """Purpose: Verify emoji content is handled correctly during truncation."""
        content = "Newsletter content with emojis 🚀📧✨ " * 20

        result = self.summarizer.summarize(content)

        assert len(result) <= 303  # max 300 chars + "..."
        assert result.endswith("...")

        # Verify emojis are preserved in truncated part
        truncated_part = result[:-3]
        assert len(truncated_part) <= 300

    def test_content_with_only_symbols(self):
        """Purpose: Verify content with only symbols/punctuation is handled correctly."""
        content = "!@#$%^&*()_+-={}[]|\\:;\"'<>,.?/" * 15

        result = self.summarizer.summarize(content)

        assert len(result) <= 303  # max 300 chars + "..."
        assert result.endswith("...")
        assert result.startswith(content[:100])

    def test_content_with_newlines_and_spaces(self):
        """Purpose: Verify content with whitespace is handled correctly."""
        content = "Line 1\nLine 2\n\nLine 4 with spaces   \t\n" * 10

        result = self.summarizer.summarize(content)

        # Should preserve original whitespace in truncation
        if len(content) > 300:
            assert len(result) <= 303
            assert result.endswith("...")
            assert result.startswith(content[:100])
        else:
            assert result == content

    def test_none_content_raises_error(self):
        """Purpose: Verify None input raises appropriate error."""
        with pytest.raises(TypeError):
            self.summarizer.summarize(None)

    def test_non_string_content_raises_error(self):
        """Purpose: Verify non-string input raises appropriate error."""
        with pytest.raises(TypeError):
            self.summarizer.summarize(123)

        with pytest.raises(TypeError):
            self.summarizer.summarize(["list", "content"])
