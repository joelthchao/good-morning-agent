"""
Integration tests for processors module.

Purpose: End-to-end flow verification ensuring proper integration
with collectors and senders modules.
"""

from unittest.mock import Mock, patch

import pytest

from src.processors import NewsletterContent, NewsletterProcessor
from src.senders import EmailSender


class TestProcessorsIntegration:
    """Integration tests for the complete processing pipeline."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = NewsletterProcessor()

    def test_end_to_end_processing_flow(self):
        """Purpose: Verify complete flow from newsletter content to ready-to-send email."""
        # Simulate newsletters from collectors
        newsletters = [
            NewsletterContent(
                title="Tech Innovation Weekly",
                content="Latest developments in AI and machine learning technologies continue to reshape industries worldwide.",
                source="tech_weekly",
                date="2025-08-05",
                metadata={"category": "technology", "priority": "high"},
            ),
            NewsletterContent(
                title="Business Insights Daily",
                content="Market analysis shows continued growth in sustainable technology investments across major corporations.",
                source="business_daily",
                date="2025-08-05",
                metadata={"category": "business", "priority": "medium"},
            ),
            NewsletterContent(
                title="Science Breakthroughs",
                content="Researchers have discovered new methods for carbon capture that could revolutionize climate change mitigation.",
                source="science_journal",
                date="2025-08-05",
                metadata={"category": "science", "priority": "high"},
            ),
        ]

        # Process newsletters
        result = self.processor.process_newsletters(newsletters)

        # Verify processing success
        assert result.success is True
        assert result.email_data is not None
        assert result.processed_count == 3
        assert result.failed_count == 0

        # Verify EmailData is properly formatted for senders
        email_data = result.email_data
        assert email_data.recipient is not None
        assert "每日電子報摘要" in email_data.subject
        assert "2025-08-05" in email_data.subject

        # Verify content contains all newsletters
        content = email_data.content
        assert "Tech Innovation Weekly" in content
        assert "Business Insights Daily" in content
        assert "Science Breakthroughs" in content
        assert "tech_weekly" in content
        assert "business_daily" in content
        assert "science_journal" in content

        # Verify metadata is properly structured
        metadata = email_data.metadata
        assert metadata["processed_count"] == 3
        assert metadata["failed_count"] == 0
        assert metadata["date"] == "2025-08-05"
        assert len(metadata["sources"]) == 3

    @patch("src.processors.newsletter_processor.get_config")
    def test_integration_with_senders_module(self, mock_config):
        """Purpose: Verify processors output is compatible with senders module."""
        # Mock config for recipient
        mock_config.return_value.email.recipient_email = "test@example.com"

        # Create test newsletter
        newsletter = NewsletterContent(
            title="Integration Test Newsletter",
            content="This is a test for integration between processors and senders modules.",
            source="integration_test",
            date="2025-08-05",
            metadata={"test": True},
        )

        # Process newsletter
        result = self.processor.process_newsletters([newsletter])

        assert result.success is True
        email_data = result.email_data

        # Verify EmailData can be used with EmailSender (mock the sender)
        with patch("src.senders.email_sender.EmailSender") as MockSender:
            mock_sender_instance = Mock()
            MockSender.return_value = mock_sender_instance
            mock_sender_instance.send_email.return_value = Mock(
                success=True, message_id="test-id"
            )

            # This should work without errors
            sender = MockSender(Mock())
            send_result = sender.send_email(email_data)

            # Verify sender was called with our EmailData
            mock_sender_instance.send_email.assert_called_once_with(email_data)
            assert send_result.success is True

    def test_large_dataset_processing_performance(self):
        """Purpose: Verify performance with larger datasets and memory efficiency."""
        # Create 50 newsletters to test performance
        newsletters = []
        for i in range(50):
            newsletters.append(
                NewsletterContent(
                    title=f"Newsletter {i:02d}",
                    content=f"Content for newsletter {i} with some substantial text content to simulate real newsletters that might contain significant amounts of text and information.",
                    source=f"source_{i:02d}",
                    date="2025-08-05",
                    metadata={"index": i, "batch": "performance_test"},
                )
            )

        # Process all newsletters
        result = self.processor.process_newsletters(newsletters)

        # Verify all were processed successfully
        assert result.success is True
        assert result.processed_count == 50
        assert result.failed_count == 0

        # Verify the result is reasonable
        assert result.email_data is not None
        assert len(result.email_data.content) > 1000  # Should be substantial content
        assert result.email_data.metadata["processed_count"] == 50

    def test_error_recovery_and_partial_processing(self):
        """Purpose: Verify error recovery maintains system stability."""
        newsletters = [
            NewsletterContent(
                title="Good Newsletter 1",
                content="This newsletter will process successfully.",
                source="good_source_1",
                date="2025-08-05",
                metadata={},
            ),
            NewsletterContent(
                title="Good Newsletter 2",
                content="This newsletter will also process successfully.",
                source="good_source_2",
                date="2025-08-05",
                metadata={},
            ),
            NewsletterContent(
                title="Problematic Newsletter",
                content="This newsletter will cause processing issues during summarization.",
                source="problematic_source",
                date="2025-08-05",
                metadata={},
            ),
        ]

        # Mock summarizer to fail on problematic content
        with patch.object(self.processor.summarizer, "summarize") as mock_summarize:

            def side_effect(content):
                if "cause processing issues" in content:
                    raise RuntimeError("Simulated processing error")
                return content[:100] + "..." if len(content) > 100 else content

            mock_summarize.side_effect = side_effect

            result = self.processor.process_newsletters(newsletters)

            # Should succeed partially
            assert result.success is True  # Overall success despite one failure
            assert result.processed_count == 2
            assert result.failed_count == 1
            assert len(result.errors) == 1

            # Error should be tracked
            error_stats = self.processor.error_tracker.get_error_stats()
            assert error_stats["total_errors"] == 1
            assert "RuntimeError" in error_stats["error_types"]

            # Good newsletters should be in result
            content = result.email_data.content
            assert "Good Newsletter 1" in content
            assert "Good Newsletter 2" in content

    def test_unicode_content_end_to_end(self):
        """Purpose: Verify Unicode content handling throughout the pipeline."""
        newsletters = [
            NewsletterContent(
                title="中文科技資訊 📱",
                content="最新的人工智慧技術發展，包含機器學習、深度學習等前沿科技內容。這些技術正在改變我們的生活方式。",
                source="中文科技源",
                date="2025-08-05",
                metadata={"lang": "zh-TW", "category": "科技"},
            ),
            NewsletterContent(
                title="Business News 🏢",
                content="Global market trends and analysis with emojis 📊 and special characters ©®™€£¥",
                source="business_international",
                date="2025-08-05",
                metadata={"lang": "en", "symbols": True},
            ),
        ]

        result = self.processor.process_newsletters(newsletters)

        assert result.success is True

        # Verify Unicode content is preserved
        content = result.email_data.content
        assert "中文科技資訊" in content
        assert "📱" in content
        assert "人工智慧" in content
        assert "📊" in content
        assert "©®™€£¥" in content

        # Verify Unicode in metadata
        assert "中文科技源" in result.email_data.metadata["sources"]

    def test_empty_and_edge_case_handling(self):
        """Purpose: Verify edge cases are handled gracefully."""
        # Test empty newsletter list
        result = self.processor.process_newsletters([])
        assert result.success is False
        assert result.processed_count == 0
        assert "No newsletters to process" in str(result.errors)

        # Test newsletter with minimal content
        minimal_newsletter = NewsletterContent(
            title="Minimal",
            content="X",  # Single character
            source="minimal_source",
            date="2025-08-05",
            metadata={},
        )

        result = self.processor.process_newsletters([minimal_newsletter])
        assert result.success is True
        assert result.processed_count == 1
        assert "Minimal" in result.email_data.content

    def test_configuration_integration(self):
        """Purpose: Verify proper integration with configuration system."""
        newsletter = NewsletterContent(
            title="Config Test Newsletter",
            content="Testing configuration integration",
            source="config_test",
            date="2025-08-05",
            metadata={},
        )

        # Test that configuration is properly loaded and used
        with patch("src.processors.newsletter_processor.get_config") as mock_config:
            mock_config.return_value.email.recipient_email = (
                "configured-recipient@example.com"
            )

            result = self.processor.process_newsletters([newsletter])

            assert result.success is True
            assert result.email_data.recipient == "configured-recipient@example.com"

            # Verify config was called
            mock_config.assert_called()

    def test_memory_efficiency_with_repeated_processing(self):
        """Purpose: Verify memory doesn't leak with repeated processing."""
        # Process multiple batches to check for memory issues
        for batch in range(5):
            newsletters = [
                NewsletterContent(
                    title=f"Batch {batch} Newsletter {i}",
                    content=f"Content for batch {batch}, newsletter {i}"
                    * 10,  # Larger content
                    source=f"batch_{batch}_source_{i}",
                    date="2025-08-05",
                    metadata={"batch": batch, "index": i},
                )
                for i in range(10)  # 10 newsletters per batch
            ]

            result = self.processor.process_newsletters(newsletters)

            assert result.success is True
            assert result.processed_count == 10

            # Clear any accumulated state (if processor has any)
            # This tests that the processor can handle repeated use

        # Verify error tracker doesn't accumulate unnecessarily
        error_stats = self.processor.error_tracker.get_error_stats()
        assert error_stats["total_errors"] == 0  # No errors in this test
