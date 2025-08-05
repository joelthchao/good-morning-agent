"""
Error tracking and backlog management for newsletter processing.

This module tracks processing failures and maintains a backlog
for future improvement and debugging.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class ErrorTracker:
    """Tracks errors and maintains a backlog of failed processing attempts."""

    def __init__(self) -> None:
        """Initialize error tracker with empty state."""
        self._errors: list[dict[str, Any]] = []
        self._error_counts: dict[str, int] = {}

    def record_error(self, newsletter_title: str, error: Exception) -> None:
        """
        Record a processing error for a newsletter.

        Args:
            newsletter_title: Title of the newsletter that failed
            error: Exception that occurred during processing
        """
        error_entry = {
            "newsletter_title": newsletter_title,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.now().isoformat(),
            "retry_count": 0,  # For future retry functionality
        }

        self._errors.append(error_entry)

        # Update error type counts
        error_type = str(error_entry["error_type"])
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1

        logger.error(f"Recorded error for '{newsletter_title}': {error}")

    def get_backlog(self) -> list[dict[str, Any]]:
        """
        Get the backlog of failed processing attempts.

        Returns:
            List of error entries with details
        """
        return self._errors.copy()

    def get_error_stats(self) -> dict[str, Any]:
        """
        Get error statistics and recent errors.

        Returns:
            Dictionary containing error statistics
        """
        return {
            "total_errors": len(self._errors),
            "error_types": self._error_counts.copy(),
            "recent_errors": (
                self._errors[-10:] if self._errors else []
            ),  # Last 10 errors
        }

    def clear_backlog(self) -> None:
        """Clear the error backlog and reset statistics."""
        self._errors.clear()
        self._error_counts.clear()
        logger.info("Error backlog cleared")
