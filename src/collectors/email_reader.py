"""
Email Reader for Good Morning Agent.

This module handles:
- IMAP connection management
- Email fetching and parsing
- Newsletter identification and filtering
- Content extraction and preprocessing
"""

import email
import imaplib
import logging
import re
import time
from datetime import datetime, timedelta
from email.header import decode_header
from email.message import EmailMessage, Message
from typing import Any

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def decode_mime_header(header_value: str) -> str:
    """
    Decode MIME encoded header value.

    Args:
        header_value: Raw header value that may contain MIME encoding

    Returns:
        Decoded header value as string
    """
    if not header_value:
        return ""

    try:
        decoded_parts = decode_header(header_value)
        decoded_string = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_string += part.decode(encoding, errors="ignore")
                else:
                    decoded_string += part.decode("utf-8", errors="ignore")
            else:
                decoded_string += str(part)

        return decoded_string.strip()
    except Exception as e:
        logger.warning(f"Failed to decode header '{header_value}': {e}")
        return header_value


def clean_content(content: str) -> str:
    """
    Clean email content by removing unwanted characters and formatting.

    Args:
        content: Raw email content

    Returns:
        Cleaned content
    """
    if not content:
        return ""

    # Remove invisible characters and control characters

    # Remove various invisible and control characters
    content = re.sub(
        r"[\u00AD\u200B\u200C\u200D\uFEFF]", "", content
    )  # Soft hyphen, zero-width chars
    content = re.sub(
        r"[\u180E\u2000-\u200F\u2028-\u202F\u205F-\u206F]", " ", content
    )  # Various spaces

    # Remove specific problematic characters found in emails
    content = re.sub(
        r"[\u00A0\u202F\u2060\u034F]", " ", content
    )  # Non-breaking spaces and invisible chars
    content = re.sub(
        r"[\u200E\u200F\u202A-\u202E]", "", content
    )  # Text direction marks
    content = re.sub(r"[\u206A-\u206F]", "", content)  # Deprecated format characters

    # Remove multiple consecutive spaces and clean whitespace
    content = re.sub(r"\s+", " ", content)
    content = content.strip()

    # Remove specific email artifacts
    content = re.sub(r"­͏+", "", content)  # Remove specific problematic sequence
    content = re.sub(
        r"^\s*[|\[\]\(\)]+\s*", "", content
    )  # Remove leading brackets/pipes

    return content


class EmailConnectionError(Exception):
    """Raised when email connection fails."""

    pass


class EmailParsingError(Exception):
    """Raised when email parsing fails."""

    pass


class EmailReader:
    """
    Email reader for collecting and processing newsletters via IMAP.

    Features:
    - Secure IMAP connection management
    - Email fetching with filtering options
    - HTML/text email parsing
    - Newsletter identification and classification
    - Content extraction and cleaning
    """

    def __init__(
        self,
        imap_server: str,
        imap_port: int,
        email_address: str,
        password: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        """
        Initialize EmailReader with connection parameters.

        Args:
            imap_server: IMAP server hostname
            imap_port: IMAP server port
            email_address: Email address for authentication
            password: App password for authentication
            max_retries: Maximum connection retry attempts
            retry_delay: Delay between retry attempts (seconds)
        """
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.email_address = email_address
        self.password = password
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.connection: imaplib.IMAP4_SSL | None = None

        # Newsletter identification patterns
        self.newsletter_patterns = {
            "sender_domains": [
                "substack.com",
                "newsletter.com",
                "mailchimp.com",
                "constantcontact.com",
                "tldrnewsletter.com",
            ],
            "subject_patterns": [
                r"newsletter",
                r"weekly",
                r"daily",
                r"digest",
                r"roundup",
                r"update",
            ],
        }

    def __enter__(self) -> "EmailReader":
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit with cleanup."""
        self.disconnect()

    def connect(self) -> None:
        """
        Establish IMAP connection with retry logic.

        Raises:
            EmailConnectionError: If connection fails after max retries
        """
        for attempt in range(self.max_retries):
            try:
                logger.info(
                    f"Connecting to IMAP server {self.imap_server}:{self.imap_port}"
                )
                self.connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)

                # Authenticate
                result, data = self.connection.login(self.email_address, self.password)
                if result != "OK":
                    raise EmailConnectionError(f"Authentication failed: {data}")

                logger.info("IMAP connection established successfully")
                return

            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2**attempt))  # Exponential backoff
                else:
                    raise EmailConnectionError(
                        f"Failed to connect after {self.max_retries} attempts: {e}"
                    ) from e

    def disconnect(self) -> None:
        """Safely disconnect from IMAP server."""
        if self.connection:
            try:
                self.connection.logout()
                logger.info("IMAP connection closed")
            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.connection = None

    def select_mailbox(self, mailbox: str = "INBOX") -> tuple[str, int]:
        """
        Select mailbox and return status and message count.

        Args:
            mailbox: Mailbox name to select

        Returns:
            Tuple of (status, message_count)

        Raises:
            EmailConnectionError: If no connection or selection fails
        """
        if not self.connection:
            raise EmailConnectionError("No active IMAP connection")

        result, data = self.connection.select(mailbox)
        if result != "OK":
            raise EmailConnectionError(f"Failed to select mailbox {mailbox}: {data}")

        message_count = int(data[0]) if data and data[0] else 0
        logger.info(f"Selected mailbox '{mailbox}' with {message_count} messages")

        return result, message_count

    def search_emails(
        self,
        criteria: str = "ALL",
        unread_only: bool = False,
        since_date: datetime | None = None,
    ) -> list[str]:
        """
        Search for emails matching criteria.

        Args:
            criteria: IMAP search criteria
            unread_only: Only return unread emails
            since_date: Only return emails since this date

        Returns:
            List of email UIDs

        Raises:
            EmailConnectionError: If no connection or search fails
        """
        if not self.connection:
            raise EmailConnectionError("No active IMAP connection")

        # Build search criteria
        search_parts = []

        if unread_only:
            search_parts.append("UNSEEN")

        if since_date:
            date_str = since_date.strftime("%d-%b-%Y")
            search_parts.append(f"SINCE {date_str}")

        if search_parts:
            criteria = " ".join(search_parts)

        logger.debug(f"Searching emails with criteria: {criteria}")

        result, data = self.connection.search(None, criteria)
        if result != "OK":
            raise EmailConnectionError(f"Email search failed: {data}")

        # Parse UIDs from response
        uids = data[0].decode().split() if data[0] else []
        logger.info(f"Found {len(uids)} emails matching criteria")

        return uids

    def fetch_email(self, uid: str) -> dict[str, Any] | None:
        """
        Fetch and parse a single email by UID.

        Args:
            uid: Email UID to fetch

        Returns:
            Dictionary containing parsed email data or None if failed
        """
        if not self.connection:
            raise EmailConnectionError("No active IMAP connection")

        try:
            # Fetch email data
            result, data = self.connection.fetch(uid, "(RFC822)")
            if result != "OK" or not data:
                logger.warning(f"Failed to fetch email UID {uid}")
                return None

            # Parse email message
            raw_data = data[0][1] if isinstance(data[0], tuple) else data[0]
            if not isinstance(raw_data, bytes | bytearray):
                logger.warning(f"Invalid email data type for UID {uid}")
                return None
            email_message = email.message_from_bytes(raw_data)

            return self._parse_email_message(email_message, uid)

        except Exception as e:
            logger.error(f"Error fetching email UID {uid}: {e}")
            return None

    def fetch_emails(
        self,
        limit: int | None = None,
        unread_only: bool = False,
        since_date: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch multiple emails with optional filtering.

        Args:
            limit: Maximum number of emails to fetch
            unread_only: Only fetch unread emails
            since_date: Only fetch emails since this date

        Returns:
            List of parsed email dictionaries
        """
        # Search for matching emails
        uids = self.search_emails(
            unread_only=unread_only,
            since_date=since_date,
        )

        # Apply limit
        if limit and len(uids) > limit:
            uids = uids[-limit:]  # Get most recent emails

        # Fetch and parse emails
        emails = []
        for uid in uids:
            email_data = self.fetch_email(uid)
            if email_data:
                emails.append(email_data)

        logger.info(f"Successfully fetched {len(emails)} emails")
        return emails

    def _parse_email_message(
        self, message: EmailMessage | Message, uid: str
    ) -> dict[str, Any]:
        """
        Parse email message into structured data.

        Args:
            message: Email message object
            uid: Email UID

        Returns:
            Dictionary with email data

        Raises:
            EmailParsingError: If parsing fails
        """
        try:
            # Extract basic metadata with proper decoding
            email_data = {
                "uid": uid,
                "subject": decode_mime_header(message.get("Subject", "")),
                "sender": decode_mime_header(message.get("From", "")),
                "date": message.get("Date", ""),
                "content_type": "",
                "body": "",
                "text_content": "",
                "html_content": "",
                "is_newsletter": False,
                "newsletter_type": "",
                "message_id": message.get("Message-ID", ""),
            }

            # Extract body content
            if message.is_multipart():
                for part in message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))

                    # Skip attachments
                    if "attachment" in content_disposition:
                        continue

                    if content_type == "text/plain":
                        payload = part.get_payload(decode=True)
                        raw_content = (
                            payload.decode("utf-8", errors="ignore")
                            if isinstance(payload, bytes)
                            else str(payload)
                        )
                        email_data["text_content"] = clean_content(raw_content)
                    elif content_type == "text/html":
                        payload = part.get_payload(decode=True)
                        raw_content = (
                            payload.decode("utf-8", errors="ignore")
                            if isinstance(payload, bytes)
                            else str(payload)
                        )
                        email_data["html_content"] = clean_content(raw_content)
            else:
                content_type = message.get_content_type()
                email_data["content_type"] = content_type
                payload = message.get_payload(decode=True)
                body = (
                    payload.decode("utf-8", errors="ignore")
                    if isinstance(payload, bytes)
                    else str(payload)
                )

                if content_type == "text/html":
                    email_data["html_content"] = body
                else:
                    email_data["text_content"] = body

            # Determine primary content
            if email_data["html_content"]:
                email_data["body"] = email_data["html_content"]
                email_data["content_type"] = "text/html"
                # Extract text from HTML for fallback
                soup = BeautifulSoup(str(email_data["html_content"]), "html.parser")
                email_data["text_content"] = soup.get_text()
            else:
                email_data["body"] = email_data["text_content"]
                email_data["content_type"] = "text/plain"

            # Identify if this is a newsletter
            email_data["is_newsletter"] = self._is_newsletter(email_data)

            if email_data["is_newsletter"]:
                email_data["newsletter_type"] = self._classify_newsletter(email_data)

            return email_data

        except Exception as e:
            raise EmailParsingError(f"Failed to parse email UID {uid}: {e}") from e

    def _is_newsletter(self, email_data: dict[str, Any]) -> bool:
        """
        Determine if an email is a newsletter.

        Args:
            email_data: Parsed email data

        Returns:
            True if email appears to be a newsletter
        """
        sender = email_data["sender"].lower()
        subject = email_data["subject"].lower()

        # Check sender domain patterns
        for domain in self.newsletter_patterns["sender_domains"]:
            if domain in sender:
                return True

        # Check subject patterns
        for pattern in self.newsletter_patterns["subject_patterns"]:
            if re.search(pattern, subject, re.IGNORECASE):
                return True

        # Additional heuristics
        body_lower = email_data["text_content"].lower()
        newsletter_indicators = [
            "unsubscribe",
            "newsletter",
            "weekly digest",
            "daily update",
            "view in browser",
        ]

        indicator_count = sum(
            1 for indicator in newsletter_indicators if indicator in body_lower
        )

        # If 2 or more indicators present, likely a newsletter
        return indicator_count >= 2

    def _classify_newsletter(self, email_data: dict[str, Any]) -> str:
        """
        Classify newsletter type based on content.

        Args:
            email_data: Parsed email data

        Returns:
            Newsletter type classification
        """
        subject = email_data["subject"].lower()
        sender = email_data["sender"].lower()

        # Technology newsletters
        tech_keywords = [
            "ai",
            "tech",
            "engineering",
            "software",
            "coding",
            "developer",
            "startup",
        ]
        if any(keyword in subject or keyword in sender for keyword in tech_keywords):
            return "technology"

        # Business/Finance newsletters
        business_keywords = ["business", "finance", "market", "economy", "investment"]
        if any(
            keyword in subject or keyword in sender for keyword in business_keywords
        ):
            return "business"

        # News newsletters
        news_keywords = ["news", "daily", "breaking", "update", "headlines"]
        if any(keyword in subject or keyword in sender for keyword in news_keywords):
            return "news"

        return "general"

    def filter_newsletters(self, emails: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Filter emails to return only newsletters, ordered by priority.

        Args:
            emails: List of email data dictionaries

        Returns:
            Filtered and sorted list of newsletter emails
        """
        newsletters = [email for email in emails if email["is_newsletter"]]

        # Priority order: newsletters > weather > news
        type_priority = {
            "technology": 1,
            "business": 2,
            "general": 3,
            "news": 4,
        }

        # Sort by priority, then by date (most recent first)
        newsletters.sort(
            key=lambda x: (
                type_priority.get(x["newsletter_type"], 5),
                x["date"],
            ),
            reverse=True,
        )

        logger.info(
            f"Filtered {len(newsletters)} newsletters from {len(emails)} emails"
        )
        return newsletters

    def get_recent_newsletters(
        self,
        days: int = 1,
        limit: int | None = 10,
    ) -> list[dict[str, Any]]:
        """
        Get recent newsletters from the last N days.

        Args:
            days: Number of days to look back
            limit: Maximum number of newsletters to return

        Returns:
            List of recent newsletter data
        """
        since_date = datetime.now() - timedelta(days=days)

        # Select inbox
        self.select_mailbox("INBOX")

        # Fetch emails
        emails = self.fetch_emails(
            limit=(limit * 2) if limit else None,  # Fetch more to account for filtering
            since_date=since_date,
        )

        # Filter for newsletters
        newsletters = self.filter_newsletters(emails)

        # Apply final limit
        if limit:
            newsletters = newsletters[:limit]

        return newsletters
