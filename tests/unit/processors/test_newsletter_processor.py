"""
Unit tests for AI-powered newsletter processor core logic.

Tests the new batch AI processing with fallback mechanisms.
"""

from unittest.mock import Mock, patch

import pytest

from src.processors.models import NewsletterContent, ProcessingResult
from src.processors.newsletter_processor import NewsletterProcessor
from src.senders.models import EmailData


class TestNewsletterProcessor:
    """Test AI-powered NewsletterProcessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = NewsletterProcessor()

    def test_initialization(self):
        """Verify NewsletterProcessor initializes correctly with dependencies."""
        assert self.processor.summarizer is not None
        assert self.processor.error_tracker is not None

    @patch.object(NewsletterProcessor, "_create_structured_content")
    def test_process_single_newsletter_success_ai(self, mock_create_structured):
        """Test successful AI batch processing of single newsletter."""
        # Mock AI summary data
        mock_summary_data = {
            "daily_highlights": ["重點 1", "重點 2"],
            "categories": {
                "tech_innovation": {
                    "summary": "科技創新摘要",
                    "priority": "high",
                    "items": ["Tech Newsletter"],
                }
            },
            "reading_time": "預估 5 分鐘",
            "meta": {"total_sources": 1, "processing_date": "2025-08-05"},
        }

        mock_create_structured.return_value = "Structured AI content"

        # Mock successful AI summarization
        with patch.object(
            self.processor.summarizer, "summarize_newsletters"
        ) as mock_ai:
            mock_ai.return_value = mock_summary_data

            newsletter = NewsletterContent(
                title="Tech Newsletter",
                content="Latest technology updates",
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
            assert email_data.content == "Structured AI content"
            assert email_data.metadata["date"] == "2025-08-05"
            assert email_data.metadata["processed_count"] == 1

    def test_process_multiple_newsletters_success_ai(self):
        """Test successful AI batch processing of multiple newsletters."""
        # Mock AI summary data
        mock_summary_data = {
            "daily_highlights": ["重點 1", "重點 2", "重點 3"],
            "categories": {
                "tech_innovation": {
                    "summary": "Tech summary",
                    "priority": "high",
                    "items": ["Tech Newsletter"],
                },
                "business_finance": {
                    "summary": "Business summary",
                    "priority": "medium",
                    "items": ["Business Newsletter"],
                },
            },
            "reading_time": "預估 8 分鐘",
            "meta": {"total_sources": 2, "processing_date": "2025-08-05"},
        }

        with patch.object(
            self.processor.summarizer, "summarize_newsletters"
        ) as mock_ai:
            mock_ai.return_value = mock_summary_data

            newsletters = [
                NewsletterContent(
                    "Tech Newsletter",
                    "Technology content",
                    "tech_source",
                    "2025-08-05",
                    {},
                ),
                NewsletterContent(
                    "Business Newsletter",
                    "Business content",
                    "biz_source",
                    "2025-08-05",
                    {},
                ),
            ]

            result = self.processor.process_newsletters(newsletters)

            assert result.success is True
            assert result.processed_count == 2
            assert result.failed_count == 0
            assert "每日智能摘要" in result.email_data.content

    def test_process_empty_newsletter_list(self):
        """Test empty input list is handled gracefully."""
        result = self.processor.process_newsletters([])

        assert result.success is False
        assert result.email_data is None
        assert result.processed_count == 0
        assert result.failed_count == 0
        assert "No newsletters to process" in str(result.errors)

    def test_ai_batch_failure_fallback_to_individual(self):
        """Test fallback to individual processing when AI batch fails."""
        newsletter = NewsletterContent(
            title="Test Newsletter",
            content="Test content",
            source="test_source",
            date="2025-08-05",
            metadata={},
        )

        # Mock AI batch to fail, individual to succeed
        with patch.object(
            self.processor.summarizer, "summarize_newsletters"
        ) as mock_batch:
            with patch.object(
                self.processor.summarizer, "summarize"
            ) as mock_individual:
                mock_batch.side_effect = Exception("AI batch processing failed")
                mock_individual.return_value = "Individual summary"

                result = self.processor.process_newsletters([newsletter])

                assert result.success is True
                assert result.processed_count == 1
                assert result.failed_count == 0
                assert len(result.errors) == 1  # AI batch error recorded
                assert "AI batch processing failed" in result.errors[0]
                assert "Test Newsletter" in result.email_data.content

    def test_both_ai_and_individual_processing_fail(self):
        """Test complete failure when both AI and individual processing fail."""
        newsletters = [
            NewsletterContent("Newsletter 1", "Content 1", "source1", "2025-08-05", {}),
            NewsletterContent("Newsletter 2", "Content 2", "source2", "2025-08-05", {}),
        ]

        # Mock both AI batch and individual processing to fail
        with patch.object(
            self.processor.summarizer, "summarize_newsletters"
        ) as mock_batch:
            with patch.object(
                self.processor.summarizer, "summarize"
            ) as mock_individual:
                mock_batch.side_effect = Exception("AI batch failed")
                mock_individual.side_effect = Exception("Individual processing failed")

                result = self.processor.process_newsletters(newsletters)

                assert result.success is False
                assert result.email_data is None
                assert result.processed_count == 0
                assert result.failed_count == 2

    def test_partial_individual_processing_success(self):
        """Test partial success in individual processing fallback."""
        newsletters = [
            NewsletterContent(
                "Valid Newsletter", "Valid content", "valid_source", "2025-08-05", {}
            ),
            NewsletterContent(
                "Invalid Newsletter",
                "Invalid content",
                "invalid_source",
                "2025-08-05",
                {},
            ),
        ]

        # Mock AI batch to fail, individual processing to partially succeed
        with patch.object(
            self.processor.summarizer, "summarize_newsletters"
        ) as mock_batch:
            with patch.object(
                self.processor.summarizer, "summarize"
            ) as mock_individual:
                mock_batch.side_effect = Exception("AI batch failed")

                def individual_side_effect(content):
                    if "Invalid content" in content:
                        raise ValueError("Cannot process invalid content")
                    return "Processed: " + content[:50]

                mock_individual.side_effect = individual_side_effect

                result = self.processor.process_newsletters(newsletters)

                assert result.success is True  # At least one succeeded
                assert result.processed_count == 1
                assert result.failed_count == 1
                assert "Valid Newsletter" in result.email_data.content

    def test_email_data_recipient_configuration(self):
        """Test EmailData recipient is correctly configured."""
        newsletter = NewsletterContent(
            "Test Newsletter", "Test content", "test_source", "2025-08-05", {}
        )

        # Mock config to return specific recipient
        with patch("src.processors.newsletter_processor.get_config") as mock_config:
            mock_config.return_value.email.recipient_email = (
                "test-recipient@example.com"
            )

            # Mock successful AI processing
            with patch.object(
                self.processor.summarizer, "summarize_newsletters"
            ) as mock_ai:
                mock_ai.return_value = {
                    "daily_highlights": ["Test highlight"],
                    "categories": {
                        "general": {
                            "summary": "Test",
                            "priority": "high",
                            "items": ["Test Newsletter"],
                        }
                    },
                    "reading_time": "5 min",
                    "meta": {"total_sources": 1, "processing_date": "2025-08-05"},
                }

                result = self.processor.process_newsletters([newsletter])

                assert result.success is True
                assert result.email_data.recipient == "test-recipient@example.com"

    def test_structured_content_formatting(self):
        """Test structured content formatting from AI summary."""
        newsletter = NewsletterContent(
            "Newsletter A", "Content A", "source_a", "2025-08-05", {}
        )

        # Mock AI to return structured data
        mock_summary_data = {
            "daily_highlights": ["今日重點 1", "今日重點 2"],
            "categories": {
                "tech_innovation": {
                    "summary": "科技創新的重點摘要",
                    "priority": "high",
                    "items": ["Newsletter A", "AI 突破"],
                },
                "business_finance": {
                    "summary": "商業金融趨勢",
                    "priority": "medium",
                    "items": ["市場分析"],
                },
            },
            "reading_time": "預估 8 分鐘",
            "meta": {"total_sources": 1, "processing_date": "2025-08-05"},
        }

        with patch.object(
            self.processor.summarizer, "summarize_newsletters"
        ) as mock_ai:
            mock_ai.return_value = mock_summary_data

            result = self.processor.process_newsletters([newsletter])

            email_content = result.email_data.content

            # Verify structured formatting
            assert "每日智能摘要" in email_content
            assert "🎯 今日重點" in email_content
            assert "今日重點 1" in email_content
            assert "今日重點 2" in email_content
            assert "🚀 科技創新" in email_content
            assert "💰 商業金融" in email_content
            assert "科技創新的重點摘要" in email_content
            assert "商業金融趨勢" in email_content
            assert "處理統計" in email_content

    def test_error_tracking_integration(self):
        """Test errors are properly recorded in error tracker."""
        newsletter = NewsletterContent(
            "Failing Newsletter", "Content", "source", "2025-08-05", {}
        )

        # Mock both processing methods to fail
        with patch.object(
            self.processor.summarizer, "summarize_newsletters"
        ) as mock_batch:
            with patch.object(
                self.processor.summarizer, "summarize"
            ) as mock_individual:
                mock_batch.side_effect = RuntimeError("AI Processing failed")
                mock_individual.side_effect = RuntimeError(
                    "Individual processing failed"
                )

                self.processor.process_newsletters([newsletter])

                # Verify error was recorded in error tracker
                backlog = self.processor.error_tracker.get_backlog()
                assert len(backlog) >= 1

                # Check for AI batch processing error
                ai_error_found = any(
                    "AI_BATCH_PROCESSING" in error.get("newsletter_title", "")
                    for error in backlog
                )
                assert ai_error_found

    def test_create_structured_content_method(self):
        """Test _create_structured_content method directly."""
        summary_data = {
            "daily_highlights": ["重點測試 1", "重點測試 2"],
            "categories": {
                "tech_innovation": {
                    "summary": "技術創新摘要測試",
                    "priority": "high",
                    "items": ["測試項目 1", "測試項目 2"],
                }
            },
            "reading_time": "預估 6 分鐘",
            "meta": {
                "total_sources": 1,
                "processing_date": "2025-08-05 12:00:00",
                "fallback_mode": False,
            },
        }

        content = self.processor._create_structured_content(summary_data)

        assert "每日智能摘要" in content
        assert "重點測試 1" in content
        assert "重點測試 2" in content
        assert "🚀 科技創新" in content
        assert "技術創新摘要測試" in content
        assert "測試項目 1" in content
        assert "預估 6 分鐘" in content
        assert "正常" in content  # AI 模式顯示

    def test_fallback_combine_content_method(self):
        """Test _combine_content method for fallback scenarios."""
        sections = [
            "📰 Newsletter 1\n來源：source1\n\nSummary 1\n\n" + "=" * 50,
            "📰 Newsletter 2\n來源：source2\n\nSummary 2\n\n" + "=" * 50,
        ]

        content = self.processor._combine_content(sections)

        assert "每日電子報摘要" in content
        assert "本日共收集 2 份電子報" in content
        assert "Newsletter 1" in content
        assert "Newsletter 2" in content
        assert "處理電子報數量：2" in content
        assert "Good Morning Agent 自動生成" in content
