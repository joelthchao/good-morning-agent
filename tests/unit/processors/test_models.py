"""
Unit tests for processors data models.

Purpose: Verify data structure correctness and validation logic.
"""

import pytest

from src.processors.models import NewsletterContent, ProcessingResult
from src.senders.models import EmailData


class TestNewsletterContent:
    """Test NewsletterContent model."""

    def test_valid_newsletter_content(self):
        """Purpose: Verify valid NewsletterContent creation works correctly."""
        content = NewsletterContent(
            title="Test Newsletter",
            content="This is test content for the newsletter",
            source="test_source",
            date="2025-08-05",
            metadata={"type": "technology"},
        )

        assert content.title == "Test Newsletter"
        assert content.content == "This is test content for the newsletter"
        assert content.source == "test_source"
        assert content.date == "2025-08-05"
        assert content.metadata["type"] == "technology"

    def test_empty_title_raises_error(self):
        """Purpose: Ensure validation catches missing required title."""
        with pytest.raises(ValueError, match="Title is required"):
            NewsletterContent(
                title="",
                content="Content",
                source="source",
                date="2025-08-05",
                metadata={},
            )

    def test_empty_content_raises_error(self):
        """Purpose: Ensure validation catches missing required content."""
        with pytest.raises(ValueError, match="Content is required"):
            NewsletterContent(
                title="Title",
                content="",
                source="source",
                date="2025-08-05",
                metadata={},
            )

    def test_empty_source_raises_error(self):
        """Purpose: Ensure validation catches missing required source."""
        with pytest.raises(ValueError, match="Source is required"):
            NewsletterContent(
                title="Title",
                content="Content",
                source="",
                date="2025-08-05",
                metadata={},
            )

    def test_empty_date_raises_error(self):
        """Purpose: Ensure validation catches missing required date."""
        with pytest.raises(ValueError, match="Date is required"):
            NewsletterContent(
                title="Title", content="Content", source="source", date="", metadata={}
            )

    def test_unicode_content_handling(self):
        """Purpose: Verify Unicode content (Chinese, emojis) is handled correctly."""
        content = NewsletterContent(
            title="測試電子報 📧",
            content="這是中文內容測試 🚀 包含特殊字符 ©®™",
            source="unicode_test",
            date="2025-08-05",
            metadata={"lang": "zh-TW"},
        )

        assert "測試電子報" in content.title
        assert "🚀" in content.content
        assert "©®™" in content.content


class TestProcessingResult:
    """Test ProcessingResult model."""

    def test_successful_processing_result(self):
        """Purpose: Verify successful ProcessingResult creation with EmailData."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Test Subject",
            content="Test content",
            metadata={"date": "2025-08-05"},
        )

        result = ProcessingResult(
            success=True, email_data=email_data, processed_count=3, failed_count=0
        )

        assert result.success is True
        assert result.email_data == email_data
        assert result.errors == []  # Should be initialized as empty list
        assert result.processed_count == 3
        assert result.failed_count == 0

    def test_failed_processing_result(self):
        """Purpose: Verify failed ProcessingResult with error messages."""
        errors = ["Error processing newsletter 1", "Error processing newsletter 2"]

        result = ProcessingResult(
            success=False, errors=errors, processed_count=1, failed_count=2
        )

        assert result.success is False
        assert result.email_data is None
        assert result.errors == errors
        assert result.processed_count == 1
        assert result.failed_count == 2

    def test_successful_result_without_email_data_raises_error(self):
        """Purpose: Ensure validation catches successful result without EmailData."""
        with pytest.raises(
            ValueError, match="Successful processing must have email_data"
        ):
            ProcessingResult(success=True)

    def test_failed_result_without_errors_raises_error(self):
        """Purpose: Ensure validation catches failed result without error messages."""
        with pytest.raises(
            ValueError, match="Failed processing must have error messages"
        ):
            ProcessingResult(success=False)

    def test_errors_list_initialization(self):
        """Purpose: Verify errors list is properly initialized when None."""
        email_data = EmailData(
            recipient="test@example.com", subject="Test", content="Test", metadata={}
        )

        result = ProcessingResult(
            success=True,
            email_data=email_data,
            errors=None,  # Should be initialized as empty list
        )

        assert result.errors == []

    def test_mixed_success_partial_failure_result(self):
        """Purpose: Verify partial success scenario (some processed, some failed)."""
        email_data = EmailData(
            recipient="test@example.com",
            subject="Partial Success",
            content="Some content was processed",
            metadata={},
        )

        result = ProcessingResult(
            success=True,  # Overall success despite some failures
            email_data=email_data,
            errors=["Newsletter 3 failed to process"],
            processed_count=2,
            failed_count=1,
        )

        assert result.success is True
        assert result.email_data is not None
        assert len(result.errors) == 1
        assert result.processed_count == 2
        assert result.failed_count == 1
