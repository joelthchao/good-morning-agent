"""
Data models for email sending functionality.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class EmailData:
    """Data structure for email content and metadata."""

    recipient: str
    subject: str
    content: str
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate email data after initialization."""
        if not self.recipient:
            raise ValueError("Recipient is required")
        if not self.subject:
            raise ValueError("Subject is required")
        if not self.content:
            raise ValueError("Content is required")
        if "@" not in self.recipient:
            raise ValueError("Recipient must be a valid email address")


@dataclass
class SendResult:
    """Result of email sending operation."""

    success: bool
    message_id: str | None = None
    error_message: str | None = None
    retry_count: int = 0

    def __post_init__(self) -> None:
        """Validate send result after initialization."""
        if self.success and not self.message_id:
            raise ValueError("Successful send must have a message_id")
        if not self.success and not self.error_message:
            raise ValueError("Failed send must have an error_message")
