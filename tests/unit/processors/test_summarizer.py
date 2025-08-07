"""
Unit tests for AI-powered summarizer functionality.

Tests both AI summarization and fallback truncation logic.
"""

import json
from unittest.mock import Mock, patch

import pytest

from src.processors.models import NewsletterContent
from src.processors.summarizer import Summarizer


class TestSummarizer:
    """Test AI-powered Summarizer class."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock the config to avoid needing real API keys in tests
        with patch("src.processors.summarizer.get_config") as mock_config:
            mock_config.return_value.openai.api_key = "test-key"
            mock_config.return_value.openai.model = "o4-mini"
            mock_config.return_value.openai.max_tokens = 4000
            self.summarizer = Summarizer()

    @patch("src.processors.summarizer.OpenAI")
    def test_single_content_ai_summarization_success(self, mock_openai_class):
        """Test successful AI summarization of single content."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "這是一個 AI 生成的摘要"
        mock_client.chat.completions.create.return_value = mock_response

        self.summarizer.client = mock_client

        content = "This is a long newsletter content that needs summarization."
        result = self.summarizer.summarize(content)

        assert result == "這是一個 AI 生成的摘要"
        assert mock_client.chat.completions.create.called

    @patch("src.processors.summarizer.OpenAI")
    def test_single_content_ai_failure_fallback(self, mock_openai_class):
        """Test fallback to truncation when AI fails."""
        # Mock OpenAI to raise exception
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        self.summarizer.client = mock_client

        content = "This is a long newsletter content that needs summarization. " * 10
        result = self.summarizer.summarize(content)

        # Should fallback to truncation
        assert len(result) <= 303  # max 300 chars + "..."
        assert result.endswith("...")

    @patch("src.processors.summarizer.OpenAI")
    def test_multiple_newsletters_ai_summarization_success(self, mock_openai_class):
        """Test successful AI summarization of multiple newsletters."""
        # Mock OpenAI response with structured JSON
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        ai_response = {
            "daily_highlights": ["重點 1", "重點 2", "重點 3"],
            "categories": {
                "tech_innovation": {
                    "summary": "科技創新摘要",
                    "priority": "high",
                    "items": ["項目 1", "項目 2"],
                },
                "business_finance": {
                    "summary": "商業金融摘要",
                    "priority": "medium",
                    "items": ["項目 3"],
                },
            },
            "reading_time": "預估 8 分鐘",
            "meta": {"total_sources": 2, "processing_date": "2024-01-01 12:00:00"},
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            ai_response, ensure_ascii=False
        )
        mock_client.chat.completions.create.return_value = mock_response

        self.summarizer.client = mock_client

        newsletters = [
            NewsletterContent(
                title="Tech Newsletter",
                content="AI breakthrough content",
                source="tech@example.com",
                date="2024-01-01",
                metadata={},
            ),
            NewsletterContent(
                title="Business Newsletter",
                content="Market analysis content",
                source="business@example.com",
                date="2024-01-01",
                metadata={},
            ),
        ]

        result = self.summarizer.summarize_newsletters(newsletters)

        assert result["daily_highlights"] == ["重點 1", "重點 2", "重點 3"]
        assert "tech_innovation" in result["categories"]
        assert "business_finance" in result["categories"]
        assert result["meta"]["total_sources"] == 2

    @patch("src.processors.summarizer.OpenAI")
    def test_multiple_newsletters_ai_json_parse_failure(self, mock_openai_class):
        """Test fallback when AI returns invalid JSON."""
        # Mock OpenAI to return invalid JSON
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_client.chat.completions.create.return_value = mock_response

        self.summarizer.client = mock_client

        newsletters = [
            NewsletterContent(
                title="Test Newsletter",
                content="Test content",
                source="test@example.com",
                date="2024-01-01",
                metadata={},
            )
        ]

        result = self.summarizer.summarize_newsletters(newsletters)

        # Should return fallback structure
        assert "daily_highlights" in result
        assert "categories" in result
        assert result["meta"]["fallback_mode"] is True

    def test_multiple_newsletters_empty_list_raises_error(self):
        """Test that empty newsletter list raises ValueError."""
        with pytest.raises(ValueError, match="Newsletters list cannot be empty"):
            self.summarizer.summarize_newsletters([])

    def test_fallback_summarize_truncation_logic(self):
        """Test fallback truncation logic for edge cases."""
        # Test content longer than 300 chars
        long_content = "This is a very long newsletter content. " * 20
        result = self.summarizer._fallback_summarize(long_content)

        assert len(result) <= 303  # max 300 chars + "..."
        assert result.endswith("...")

    def test_fallback_summarize_short_content_preserved(self):
        """Test fallback preserves short content completely."""
        short_content = "This is a short newsletter content."
        result = self.summarizer._fallback_summarize(short_content)

        assert result == short_content
        assert not result.endswith("...")

    def test_fallback_summarize_unicode_handling(self):
        """Test fallback handles Unicode content correctly."""
        unicode_content = "測試中文內容處理" * 50
        result = self.summarizer._fallback_summarize(unicode_content)

        assert len(result) <= 303  # max 300 chars + "..."
        assert result.endswith("...")
        # Should not corrupt Unicode characters
        truncated_part = result[:-3]
        assert len(truncated_part) <= 300

    def test_create_combined_content_structure(self):
        """Test combined content structure for AI processing."""
        newsletters = [
            NewsletterContent(
                title="Newsletter 1",
                content="Content 1",
                source="source1@example.com",
                date="2024-01-01",
                metadata={},
            ),
            NewsletterContent(
                title="Newsletter 2",
                content="Content 2",
                source="source2@example.com",
                date="2024-01-01",
                metadata={},
            ),
        ]

        result = self.summarizer._create_combined_content(newsletters)

        assert "=== 電子報 1: Newsletter 1 ===" in result
        assert "=== 電子報 2: Newsletter 2 ===" in result
        assert "來源: source1@example.com" in result
        assert "來源: source2@example.com" in result
        assert "Content 1" in result
        assert "Content 2" in result

    def test_create_fallback_summary_structure(self):
        """Test fallback summary structure when AI fails."""
        newsletters = [
            NewsletterContent(
                title="Test Newsletter",
                content="Test content for fallback",
                source="test@example.com",
                date="2024-01-01",
                metadata={},
            )
        ]

        result = self.summarizer._create_fallback_summary(newsletters)

        assert "daily_highlights" in result
        assert "categories" in result
        assert "general" in result["categories"]
        assert result["meta"]["fallback_mode"] is True
        assert result["meta"]["total_sources"] == 1

    def test_none_content_raises_error(self):
        """Test None input raises appropriate error."""
        with pytest.raises(TypeError):
            self.summarizer.summarize(None)

    def test_non_string_content_raises_error(self):
        """Test non-string input raises appropriate error."""
        with pytest.raises(TypeError):
            self.summarizer.summarize(123)

        with pytest.raises(TypeError):
            self.summarizer.summarize(["list", "content"])
