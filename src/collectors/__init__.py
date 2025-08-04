"""
Email collection module for Good Morning Agent.

This module handles collecting emails from various sources,
primarily focused on newsletter aggregation via IMAP.
"""

from .email_reader import EmailReader

__all__ = ["EmailReader"]
