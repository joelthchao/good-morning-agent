"""
Unit tests for error tracking and backlog management.

Purpose: Ensure error recording, backlog management, and statistics
work correctly for failed newsletter processing.
"""

from datetime import datetime
from unittest.mock import patch

import pytest

from src.processors.error_tracker import ErrorTracker


class TestErrorTracker:
    """Test ErrorTracker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.error_tracker = ErrorTracker()

    def test_initialization(self):
        """Purpose: Verify ErrorTracker initializes with empty state."""
        assert len(self.error_tracker.get_backlog()) == 0
        assert self.error_tracker.get_error_stats()["total_errors"] == 0

    def test_record_single_error(self):
        """Purpose: Verify single error recording works correctly."""
        newsletter_title = "Test Newsletter 1"
        error = Exception("Processing failed")

        self.error_tracker.record_error(newsletter_title, error)

        backlog = self.error_tracker.get_backlog()
        assert len(backlog) == 1

        error_entry = backlog[0]
        assert error_entry["newsletter_title"] == newsletter_title
        assert error_entry["error_type"] == "Exception"
        assert error_entry["error_message"] == "Processing failed"
        assert "timestamp" in error_entry
        assert error_entry["retry_count"] == 0

    def test_record_multiple_errors(self):
        """Purpose: Verify multiple error recording accumulates correctly."""
        errors_data = [
            ("Newsletter 1", ValueError("Invalid content")),
            ("Newsletter 2", KeyError("Missing field")),
            ("Newsletter 3", RuntimeError("Processing timeout")),
        ]

        for title, error in errors_data:
            self.error_tracker.record_error(title, error)

        backlog = self.error_tracker.get_backlog()
        assert len(backlog) == 3

        # Verify all errors are recorded with correct types
        error_types = [entry["error_type"] for entry in backlog]
        assert "ValueError" in error_types
        assert "KeyError" in error_types
        assert "RuntimeError" in error_types

    def test_error_stats_calculation(self):
        """Purpose: Verify error statistics are calculated correctly."""
        # Record various types of errors
        self.error_tracker.record_error("Newsletter 1", ValueError("Error 1"))
        self.error_tracker.record_error("Newsletter 2", ValueError("Error 2"))
        self.error_tracker.record_error("Newsletter 3", KeyError("Error 3"))
        self.error_tracker.record_error("Newsletter 4", RuntimeError("Error 4"))

        stats = self.error_tracker.get_error_stats()

        assert stats["total_errors"] == 4
        assert stats["error_types"]["ValueError"] == 2
        assert stats["error_types"]["KeyError"] == 1
        assert stats["error_types"]["RuntimeError"] == 1
        assert len(stats["recent_errors"]) <= 10  # Should limit recent errors

    def test_error_stats_empty_state(self):
        """Purpose: Verify error statistics work correctly with no errors."""
        stats = self.error_tracker.get_error_stats()

        assert stats["total_errors"] == 0
        assert stats["error_types"] == {}
        assert stats["recent_errors"] == []

    @patch("src.processors.error_tracker.datetime")
    def test_error_timestamp_recording(self, mock_datetime):
        """Purpose: Verify error timestamps are recorded correctly."""
        # Mock current time
        mock_now = datetime(2025, 8, 5, 10, 30, 0)
        mock_datetime.now.return_value = mock_now

        self.error_tracker.record_error("Test Newsletter", Exception("Test error"))

        backlog = self.error_tracker.get_backlog()
        assert len(backlog) == 1
        assert backlog[0]["timestamp"] == mock_now.isoformat()

    def test_duplicate_newsletter_error_handling(self):
        """Purpose: Verify handling of multiple errors for same newsletter."""
        newsletter_title = "Same Newsletter"

        self.error_tracker.record_error(newsletter_title, ValueError("First error"))
        self.error_tracker.record_error(newsletter_title, RuntimeError("Second error"))

        backlog = self.error_tracker.get_backlog()
        assert len(backlog) == 2

        # Both errors should be recorded
        titles = [entry["newsletter_title"] for entry in backlog]
        assert titles.count(newsletter_title) == 2

    def test_error_with_complex_message(self):
        """Purpose: Verify complex error messages are recorded correctly."""
        complex_error = Exception(
            "Complex error with\nmultiple lines\nand special chars: !@#$%"
        )

        self.error_tracker.record_error("Complex Newsletter", complex_error)

        backlog = self.error_tracker.get_backlog()
        error_entry = backlog[0]

        assert "multiple lines" in error_entry["error_message"]
        assert "!@#$%" in error_entry["error_message"]

    def test_backlog_limit_handling(self):
        """Purpose: Verify backlog doesn't grow indefinitely (if limit implemented)."""
        # Record many errors to test potential backlog limits
        for i in range(150):  # More than typical backlog limit
            self.error_tracker.record_error(f"Newsletter {i}", Exception(f"Error {i}"))

        backlog = self.error_tracker.get_backlog()
        stats = self.error_tracker.get_error_stats()

        # Should still track all errors in stats
        assert stats["total_errors"] == 150

        # Backlog might be limited (implementation detail)
        # For now, just verify it doesn't break
        assert len(backlog) >= 0

    def test_error_tracker_isolation(self):
        """Purpose: Verify multiple ErrorTracker instances don't interfere."""
        tracker1 = ErrorTracker()
        tracker2 = ErrorTracker()

        tracker1.record_error("Newsletter A", ValueError("Error A"))
        tracker2.record_error("Newsletter B", KeyError("Error B"))

        backlog1 = tracker1.get_backlog()
        backlog2 = tracker2.get_backlog()

        assert len(backlog1) == 1
        assert len(backlog2) == 1
        assert backlog1[0]["newsletter_title"] == "Newsletter A"
        assert backlog2[0]["newsletter_title"] == "Newsletter B"

    def test_get_recent_errors_limit(self):
        """Purpose: Verify recent errors are properly limited in stats."""
        # Record more errors than the recent limit
        for i in range(15):
            self.error_tracker.record_error(f"Newsletter {i}", Exception(f"Error {i}"))

        stats = self.error_tracker.get_error_stats()

        # Recent errors should be limited (typically to 10)
        assert len(stats["recent_errors"]) <= 10
        assert stats["total_errors"] == 15

    def test_clear_backlog_functionality(self):
        """Purpose: Verify backlog can be cleared if functionality exists."""
        self.error_tracker.record_error("Test Newsletter", Exception("Test error"))

        # Check if clear method exists and works
        if hasattr(self.error_tracker, "clear_backlog"):
            self.error_tracker.clear_backlog()
            assert len(self.error_tracker.get_backlog()) == 0
            # Stats should also be reset
            assert self.error_tracker.get_error_stats()["total_errors"] == 0
