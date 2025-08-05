"""
Simple summarizer for newsletter content.

This module provides basic summarization by truncating content to 100 characters,
serving as a placeholder for future AI-based summarization.
"""

import logging

logger = logging.getLogger(__name__)


class Summarizer:
    """Simple content summarizer using character truncation."""

    def summarize(self, content: str) -> str:
        """
        Summarize content by truncating to 300 characters with smart sentence ending.

        Args:
            content: Text content to summarize

        Returns:
            Summarized content (max 300 chars, ending at sentence boundary if possible)

        Raises:
            TypeError: If content is not a string
        """
        if not isinstance(content, str):
            raise TypeError("Content must be a string")

        # Use 300 characters for better readability
        max_length = 300

        if len(content) <= max_length:
            return content

        # Try to find a good breaking point (sentence end)
        truncated = content[:max_length]

        # Look for sentence endings within the last 50 characters
        sentence_endings = [".", "!", "?", "。", "！", "？"]
        best_break = -1

        for i in range(len(truncated) - 1, max(len(truncated) - 50, 0), -1):
            if truncated[i] in sentence_endings and i < len(truncated) - 1:
                # Make sure it's not just an abbreviation
                if truncated[i] == "." and i > 0 and truncated[i - 1].isupper():
                    continue
                best_break = i + 1
                break

        if best_break > 0:
            return truncated[:best_break].strip() + "..."
        else:
            # No good sentence break found, just truncate
            return truncated.rstrip() + "..."
