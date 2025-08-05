"""
Data models for newsletter processing.

These models provide a clean interface for processors,
decoupled from email structure complexity.
"""

from dataclasses import dataclass
from typing import Any

from src.senders.models import EmailData


@dataclass
class NewsletterContent:
    """Decoupled newsletter content structure."""

    title: str
    content: str
    source: str
    date: str
    metadata: dict[str, Any]

    def __post_init__(self) -> None:
        """Validate newsletter content after initialization."""
        if not self.title:
            raise ValueError("Title is required")
        if not self.content:
            raise ValueError("Content is required")
        if not self.source:
            raise ValueError("Source is required")
        if not self.date:
            raise ValueError("Date is required")


@dataclass
class ProcessingResult:
    """Result of newsletter processing operation."""

    success: bool
    email_data: EmailData | None = None
    errors: list[str] | None = None
    processed_count: int = 0
    failed_count: int = 0

    def __post_init__(self) -> None:
        """Initialize default values and validate result."""
        if self.errors is None:
            self.errors = []

        if self.success and not self.email_data:
            raise ValueError("Successful processing must have email_data")
        if not self.success and not self.errors:
            raise ValueError("Failed processing must have error messages")
