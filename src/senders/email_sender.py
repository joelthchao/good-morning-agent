"""
Email sender implementation with retry mechanism and security measures.
"""

import logging
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import TYPE_CHECKING

from .message_formatter import MessageFormatter
from .models import EmailData, SendResult
from .security_manager import SecurityManager

if TYPE_CHECKING:
    from src.utils.config import EmailConfig

logger = logging.getLogger(__name__)


class EmailSenderError(Exception):
    """Base exception for email sender errors."""

    pass


class EmailSender:
    """Handles email sending with retry mechanism and security measures."""

    def __init__(self, email_config: "EmailConfig"):
        """
        Initialize email sender.

        Args:
            email_config: Email configuration containing SMTP settings
        """
        self.config = email_config
        self.formatter = MessageFormatter()
        self.security_manager = SecurityManager(
            send_interval=int(os.getenv("EMAIL_SEND_INTERVAL", "2"))
        )

        # Validate configuration
        self._validate_config()

    def send_email(self, email_data: EmailData) -> SendResult:
        """
        Send an email with retry mechanism.

        Args:
            email_data: Email data to send

        Returns:
            SendResult with success status and details
        """
        try:
            # Validate email data
            if (
                not email_data.recipient
                or not email_data.subject
                or not email_data.content
            ):
                return SendResult(
                    success=False,
                    error_message="Missing required email data (recipient, subject, or content)",
                    retry_count=0,
                )

            # Apply security measures
            secured_data = self.security_manager.apply_anti_spam_measures(email_data)

            # Attempt to send with retries
            return self._retry_send(secured_data, max_retries=3)

        except Exception as e:
            logger.error(f"Unexpected error in send_email: {e}")
            return SendResult(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                retry_count=0,
            )

    def validate_connection(self) -> bool:
        """
        Test SMTP connection without sending an email.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()

                # Use sender credentials if available, otherwise use main credentials
                email = self.config.sender_email or self.config.address
                password = self.config.sender_password or self.config.password

                server.login(email, password)
                logger.info("SMTP connection validation successful")
                return True

        except Exception as e:
            logger.error(f"SMTP connection validation failed: {e}")
            return False

    def _retry_send(self, email_data: EmailData, max_retries: int = 3) -> SendResult:
        """
        Send email with retry mechanism.

        Args:
            email_data: Email data to send
            max_retries: Maximum number of retry attempts

        Returns:
            SendResult with success status and details
        """
        last_error = None

        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                # Wait for rate limiting if needed
                if attempt > 0:  # Don't wait on first attempt
                    wait_time = min(2**attempt, 30)  # Exponential backoff, max 30s
                    logger.info(
                        f"Retry attempt {attempt}/{max_retries}, waiting {wait_time}s"
                    )
                    time.sleep(wait_time)

                # Check rate limits
                self.security_manager.wait_if_needed()

                # Attempt to send
                message_id = self._send_single_email(email_data)

                # Record successful send
                self.security_manager.record_send()

                logger.info(
                    f"Email sent successfully to {email_data.recipient} (attempt {attempt + 1})"
                )
                return SendResult(
                    success=True, message_id=message_id, retry_count=attempt
                )

            except Exception as e:
                last_error = str(e)
                logger.warning(f"Send attempt {attempt + 1} failed: {e}")

                # Don't retry for certain errors
                if "authentication" in str(e).lower() or "login" in str(e).lower():
                    logger.error("Authentication error - not retrying")
                    break

        # All attempts failed
        logger.error(
            f"All {max_retries + 1} send attempts failed. Last error: {last_error}"
        )
        return SendResult(
            success=False,
            error_message=last_error or "Unknown error during email sending",
            retry_count=max_retries + 1,
        )

    def _send_single_email(self, email_data: EmailData) -> str:
        """
        Send a single email without retry logic.

        Args:
            email_data: Email data to send

        Returns:
            Message ID if successful

        Raises:
            EmailSenderError: If sending fails
        """
        try:
            # Format the message content
            formatted_content = self.formatter.format_plain_text(
                email_data.content, email_data.metadata
            )

            # Create email message
            msg = MIMEMultipart()
            msg["Subject"] = email_data.subject
            msg["To"] = email_data.recipient
            msg["From"] = self.config.sender_email or self.config.address

            # Add security headers
            security_headers = self.security_manager.add_authentication_headers()
            for header, value in security_headers.items():
                msg[header] = value

            # Attach text content
            text_part = MIMEText(formatted_content, "plain", "utf-8")
            msg.attach(text_part)

            # Send the email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()

                # Use sender credentials if available, otherwise use main credentials
                email = self.config.sender_email or self.config.address
                password = self.config.sender_password or self.config.password

                server.login(email, password)

                # Send message
                server.send_message(msg)

                # Extract message ID
                message_id = msg.get("Message-ID", "unknown")

                logger.debug(f"Email sent with message ID: {message_id}")
                return message_id

        except smtplib.SMTPAuthenticationError as e:
            raise EmailSenderError(f"Authentication failed: {e}") from e
        except smtplib.SMTPRecipientsRefused as e:
            raise EmailSenderError(f"Recipient refused: {e}") from e
        except smtplib.SMTPException as e:
            raise EmailSenderError(f"SMTP error: {e}") from e
        except Exception as e:
            raise EmailSenderError(f"Unexpected error: {e}") from e

    def _validate_config(self) -> None:
        """Validate email configuration."""
        if not self.config.smtp_server:
            raise EmailSenderError("SMTP server is required")

        if not self.config.smtp_port:
            raise EmailSenderError("SMTP port is required")

        if not (self.config.sender_email or self.config.address):
            raise EmailSenderError("Sender email is required")

        if not (self.config.sender_password or self.config.password):
            raise EmailSenderError("Sender password is required")

        logger.debug("Email sender configuration validated")
