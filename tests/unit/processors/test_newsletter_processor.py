"""
Unit tests for newsletter processor core logic.

Purpose: Verify core processing logic correctness including
single/multiple newsletter handling, error scenarios, and EmailData generation.
"""

from unittest.mock import Mock, patch

import pytest

from src.processors.models import NewsletterContent, ProcessingResult
from src.processors.newsletter_processor import NewsletterProcessor
from src.senders.models import EmailData


class TestNewsletterProcessor:
    """Test NewsletterProcessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = NewsletterProcessor()

    def test_initialization(self):
        """Purpose: Verify NewsletterProcessor initializes correctly with dependencies."""
        assert self.processor.summarizer is not None
        assert self.processor.error_tracker is not None

    def test_process_single_newsletter_success(self):
        """Purpose: Verify single newsletter processing creates correct EmailData."""
        newsletter = NewsletterContent(
            title="Tech Newsletter",
            content="Latest technology updates and trends in the industry",
            source="tech_source",
            date="2025-08-05",
            metadata={"category": "technology"},
        )

        result = self.processor.process_newsletters([newsletter])

        assert result.success is True
        assert result.email_data is not None
        assert result.processed_count == 1
        assert result.failed_count == 0
        assert len(result.errors) == 0

        # Verify EmailData structure
        email_data = result.email_data
        assert email_data.subject == "📧 每日電子報摘要 - 2025-08-05"
        assert "Tech Newsletter" in email_data.content
        assert "tech_source" in email_data.content
        assert email_data.metadata["date"] == "2025-08-05"
        assert email_data.metadata["processed_count"] == 1

    def test_process_multiple_newsletters_success(self):
        """Purpose: Verify multiple newsletters are concatenated correctly."""
        newsletters = [
            NewsletterContent(
                title="Tech Newsletter",
                content="Technology content",
                source="tech_source",
                date="2025-08-05",
                metadata={"category": "tech"},
            ),
            NewsletterContent(
                title="Business Newsletter",
                content="Business content",
                source="business_source",
                date="2025-08-05",
                metadata={"category": "business"},
            ),
            NewsletterContent(
                title="Science Newsletter",
                content="Science content",
                source="science_source",
                date="2025-08-05",
                metadata={"category": "science"},
            ),
        ]

        result = self.processor.process_newsletters(newsletters)

        assert result.success is True
        assert result.email_data is not None
        assert result.processed_count == 3
        assert result.failed_count == 0

        # Verify content concatenation
        email_content = result.email_data.content
        assert "Tech Newsletter" in email_content
        assert "Business Newsletter" in email_content
        assert "Science Newsletter" in email_content
        assert "Technology content" in email_content
        assert "Business content" in email_content
        assert "Science content" in email_content

    def test_process_empty_newsletter_list(self):
        """Purpose: Verify empty input list is handled gracefully."""
        result = self.processor.process_newsletters([])

        assert result.success is False
        assert result.email_data is None
        assert result.processed_count == 0
        assert result.failed_count == 0
        assert "No newsletters to process" in str(result.errors)

    def test_process_with_partial_failures(self):
        """Purpose: Verify partial failures skip errors but process valid newsletters."""
        valid_newsletter = NewsletterContent(
            title="Valid Newsletter",
            content="Valid content",
            source="valid_source",
            date="2025-08-05",
            metadata={},
        )

        # Create newsletter that will cause processing error during summarization
        problematic_newsletter = NewsletterContent(
            title="Problematic Newsletter",
            content="Content that will cause summarization to fail",
            source="problematic_source",
            date="2025-08-05",
            metadata={},
        )

        # Mock summarizer to fail on problematic content
        with patch.object(self.processor.summarizer, "summarize") as mock_summarize:

            def side_effect(content):
                if "cause summarization to fail" in content:
                    raise ValueError("Cannot summarize problematic content")
                return content[:100] + "..." if len(content) > 100 else content

            mock_summarize.side_effect = side_effect

            newsletters = [valid_newsletter, problematic_newsletter]
            result = self.processor.process_newsletters(newsletters)

            # Should succeed overall but record the failure
            assert result.success is True  # At least one succeeded
            assert result.email_data is not None
            assert result.processed_count == 1
            assert result.failed_count == 1
            assert len(result.errors) == 1

            # Valid newsletter content should be in result
            assert "Valid Newsletter" in result.email_data.content

    def test_process_all_newsletters_fail(self):
        """Purpose: Verify all failures results in overall failure."""
        newsletters = [
            NewsletterContent(
                title="Newsletter 1",
                content="Content 1",
                source="source1",
                date="2025-08-05",
                metadata={},
            ),
            NewsletterContent(
                title="Newsletter 2",
                content="Content 2",
                source="source2",
                date="2025-08-05",
                metadata={},
            ),
        ]

        # Mock summarizer to always fail
        with patch.object(self.processor.summarizer, "summarize") as mock_summarize:
            mock_summarize.side_effect = Exception("Summarization failed")

            result = self.processor.process_newsletters(newsletters)

            assert result.success is False
            assert result.email_data is None
            assert result.processed_count == 0
            assert result.failed_count == 2
            assert len(result.errors) == 2

    def test_email_data_recipient_configuration(self):
        """Purpose: Verify EmailData recipient is correctly configured."""
        newsletter = NewsletterContent(
            title="Test Newsletter",
            content="Test content",
            source="test_source",
            date="2025-08-05",
            metadata={},
        )

        # Mock config to return specific recipient
        with patch("src.processors.newsletter_processor.get_config") as mock_config:
            mock_config.return_value.email.recipient_email = (
                "test-recipient@example.com"
            )

            result = self.processor.process_newsletters([newsletter])

            assert result.success is True
            assert result.email_data.recipient == "test-recipient@example.com"

    def test_content_formatting_structure(self):
        """Purpose: Verify content is formatted with proper structure and separators."""
        newsletters = [
            NewsletterContent(
                title="Newsletter A",
                content="Content A with multiple lines\nand formatting",
                source="source_a",
                date="2025-08-05",
                metadata={"priority": "high"},
            ),
            NewsletterContent(
                title="Newsletter B",
                content="Content B",
                source="source_b",
                date="2025-08-05",
                metadata={"priority": "low"},
            ),
        ]

        result = self.processor.process_newsletters(newsletters)

        email_content = result.email_data.content

        # Verify proper formatting and separation
        assert "Newsletter A" in email_content
        assert "Newsletter B" in email_content
        assert "source_a" in email_content
        assert "source_b" in email_content

        # Should have clear separation between newsletters
        assert "=" in email_content or "-" in email_content

    def test_metadata_aggregation(self):
        """Purpose: Verify metadata from multiple newsletters is properly aggregated."""
        newsletters = [
            NewsletterContent(
                title="Tech News",
                content="Tech content",
                source="tech_source",
                date="2025-08-05",
                metadata={"category": "technology", "priority": "high"},
            ),
            NewsletterContent(
                title="Business News",
                content="Business content",
                source="biz_source",
                date="2025-08-05",
                metadata={"category": "business", "priority": "medium"},
            ),
        ]

        result = self.processor.process_newsletters(newsletters)

        email_metadata = result.email_data.metadata

        # Should include processing statistics
        assert email_metadata["processed_count"] == 2
        assert email_metadata["failed_count"] == 0
        assert email_metadata["date"] == "2025-08-05"

        # Should include source information
        assert "sources" in email_metadata
        assert "tech_source" in email_metadata["sources"]
        assert "biz_source" in email_metadata["sources"]

    def test_unicode_content_processing(self):
        """Purpose: Verify Unicode content is processed correctly."""
        newsletter = NewsletterContent(
            title="中文電子報 📧",
            content="這是中文內容測試，包含 emojis 🚀 和特殊字符 ©®™",
            source="unicode_source",
            date="2025-08-05",
            metadata={"lang": "zh-TW"},
        )

        result = self.processor.process_newsletters([newsletter])

        assert result.success is True
        email_content = result.email_data.content

        # Verify Unicode content is preserved
        assert "中文電子報" in email_content
        assert "🚀" in email_content
        assert "©®™" in email_content

    def test_error_tracking_integration(self):
        """Purpose: Verify errors are properly recorded in error tracker."""
        newsletter = NewsletterContent(
            title="Failing Newsletter",
            content="Content that will fail",
            source="failing_source",
            date="2025-08-05",
            metadata={},
        )

        # Mock summarizer to fail
        with patch.object(self.processor.summarizer, "summarize") as mock_summarize:
            mock_summarize.side_effect = RuntimeError("Processing failed")

            self.processor.process_newsletters([newsletter])

            # Verify error was recorded in error tracker
            backlog = self.processor.error_tracker.get_backlog()
            assert len(backlog) == 1
            assert backlog[0]["newsletter_title"] == "Failing Newsletter"
            assert backlog[0]["error_type"] == "RuntimeError"
