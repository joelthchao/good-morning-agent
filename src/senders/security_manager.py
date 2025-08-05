"""
Security manager for email sending to avoid spam detection.
"""

import hashlib
import logging
import random
import time
from datetime import datetime

from .models import EmailData

logger = logging.getLogger(__name__)


class SecurityManager:
    """Manages security measures to avoid spam detection."""

    def __init__(self, send_interval: int = 2):
        """
        Initialize security manager.

        Args:
            send_interval: Minimum seconds between email sends
        """
        self.send_interval = send_interval
        self.last_send_time: float | None = None
        self.daily_send_count = 0
        self.daily_reset_time = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

    def apply_anti_spam_measures(self, email_data: EmailData) -> EmailData:
        """
        Apply anti-spam measures to email data.

        Args:
            email_data: Original email data

        Returns:
            Modified email data with anti-spam measures applied
        """
        try:
            # Create a copy to avoid modifying original
            modified_data = EmailData(
                recipient=email_data.recipient,
                subject=self._diversify_subject(email_data.subject),
                content=self._diversify_content(email_data.content),
                metadata=email_data.metadata.copy(),
            )

            # Add security metadata
            modified_data.metadata.update(
                {
                    "security_hash": self._generate_content_hash(email_data.content),
                    "send_timestamp": datetime.now().isoformat(),
                    "anti_spam_applied": True,
                }
            )

            logger.debug("Applied anti-spam measures to email")
            return modified_data

        except Exception as e:
            logger.error(f"Error applying anti-spam measures: {e}")
            return email_data

    def add_authentication_headers(self) -> dict[str, str]:
        """
        Add authentication headers to improve deliverability.

        Returns:
            Dictionary of additional email headers
        """
        return {
            "X-Mailer": "Good Morning Agent v1.0",
            "X-Priority": "3 (Normal)",
            "X-MSMail-Priority": "Normal",
            "Message-ID": self._generate_message_id(),
            "Date": datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z"),
        }

    def validate_send_frequency(self) -> bool:
        """
        Validate if it's safe to send an email based on frequency limits.

        Returns:
            True if safe to send, False otherwise
        """
        current_time = time.time()

        # Reset daily count if new day
        self._reset_daily_count_if_needed()

        # Check minimum interval between sends
        if self.last_send_time is not None:
            time_since_last = current_time - self.last_send_time
            if time_since_last < self.send_interval:
                wait_time = self.send_interval - time_since_last
                logger.warning(
                    f"Rate limit: need to wait {wait_time:.1f} seconds before next send"
                )
                return False

        # Check daily limits (configurable, default 100)
        daily_limit = 100  # Can be made configurable
        if self.daily_send_count >= daily_limit:
            logger.warning(
                f"Daily send limit reached: {self.daily_send_count}/{daily_limit}"
            )
            return False

        return True

    def wait_if_needed(self) -> None:
        """Wait if necessary to comply with rate limits."""
        if not self.validate_send_frequency():
            current_time = time.time()
            if self.last_send_time is not None:
                wait_time = self.send_interval - (current_time - self.last_send_time)
                if wait_time > 0:
                    logger.info(
                        f"Waiting {wait_time:.1f} seconds to comply with rate limits"
                    )
                    time.sleep(wait_time)

    def record_send(self) -> None:
        """Record that an email was sent for rate limiting."""
        self.last_send_time = time.time()
        self.daily_send_count += 1
        logger.debug(f"Recorded send. Daily count: {self.daily_send_count}")

    def _diversify_subject(self, subject: str) -> str:
        """Add subtle variations to subject line to avoid spam detection."""
        variations = [
            "",  # No change
            " 📧",
            " 📨",
            " ✉️",
        ]
        return subject + random.choice(variations)

    def _diversify_content(self, content: str) -> str:
        """Add subtle variations to content to avoid spam detection."""
        # Add random spacing variations (very subtle)
        diversified = content

        # Occasionally add subtle formatting variations
        if random.random() < 0.3:  # 30% chance
            variations = [
                f"\n{content}",  # Extra newline at start
                f"{content}\n",  # Extra newline at end
                content.replace("。", "。 "),  # Add space after periods sometimes
            ]
            diversified = random.choice(variations)

        return diversified

    def _generate_content_hash(self, content: str) -> str:
        """Generate a hash of the content for tracking."""
        return hashlib.md5(content.encode("utf-8")).hexdigest()[:8]

    def _generate_message_id(self) -> str:
        """Generate a unique message ID."""
        timestamp = str(int(time.time()))
        random_part = str(random.randint(1000, 9999))
        return f"<{timestamp}.{random_part}@good-morning-agent>"

    def _reset_daily_count_if_needed(self) -> None:
        """Reset daily send count if a new day has started."""
        now = datetime.now()
        current_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        if current_day > self.daily_reset_time:
            self.daily_send_count = 0
            self.daily_reset_time = current_day
            logger.debug("Reset daily send count for new day")
