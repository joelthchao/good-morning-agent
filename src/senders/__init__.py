"""
Email sending module for Good Morning Agent.

This module handles email sending functionality with anti-spam measures
and proper error handling.
"""

from .email_sender import EmailSender
from .message_formatter import MessageFormatter
from .models import EmailData, SendResult
from .security_manager import SecurityManager

__all__ = [
    "EmailSender",
    "MessageFormatter",
    "SecurityManager",
    "EmailData",
    "SendResult",
]
