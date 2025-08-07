"""
AI-powered summarizer for newsletter content.

This module provides intelligent summarization using OpenAI API,
with structured output for multiple newsletter integration.
"""

import json
import logging
from datetime import datetime
from typing import Any

from openai import OpenAI

from src.processors.models import NewsletterContent
from src.utils.config import get_config

logger = logging.getLogger(__name__)


class Summarizer:
    """AI-powered content summarizer using OpenAI API."""

    def __init__(self) -> None:
        """Initialize the summarizer with OpenAI client."""
        config = get_config()
        self.client = OpenAI(api_key=config.openai.api_key)
        self.model = config.openai.model
        self.max_tokens = config.openai.max_tokens
        logger.debug(f"AI Summarizer initialized with model: {self.model}")

    def summarize(self, content: str) -> str:
        """
        Summarize single content using AI (fallback method).

        Args:
            content: Text content to summarize

        Returns:
            Summarized content

        Raises:
            TypeError: If content is not a string
        """
        if not isinstance(content, str):
            raise TypeError("Content must be a string")

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是專業的內容摘要專家。請將提供的內容摘要為 100-150 字的重點摘要，使用繁體中文。",
                    },
                    {
                        "role": "user",
                        "content": f"請摘要以下內容：\n\n{content[:2000]}",  # 限制輸入長度
                    },
                ],
                max_tokens=300,
                temperature=0.3,
            )

            summary = response.choices[0].message.content
            if summary:
                logger.debug(f"AI summarization successful, length: {len(summary)}")
                return summary.strip()
            else:
                logger.warning("AI returned empty summary, using fallback")
                return self._fallback_summarize(content)

        except Exception as e:
            logger.error(f"AI summarization failed: {e}, using fallback")
            return self._fallback_summarize(content)

    def summarize_newsletters(
        self, newsletters: list[NewsletterContent]
    ) -> dict[str, Any]:
        """
        Summarize multiple newsletters using AI with structured output.

        Args:
            newsletters: List of newsletter content to process

        Returns:
            Structured summary dictionary with categories and highlights

        Raises:
            ValueError: If newsletters list is empty
        """
        if not newsletters:
            raise ValueError("Newsletters list cannot be empty")

        logger.info(f"Starting AI summarization for {len(newsletters)} newsletters")

        # Create combined content for AI processing
        combined_content = self._create_combined_content(newsletters)

        # Create user prompt
        user_prompt = self._create_user_prompt(newsletters, combined_content)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=self.max_tokens,
                temperature=0.3,
            )

            ai_response = response.choices[0].message.content
            if not ai_response:
                logger.error("AI returned empty response")
                return self._create_fallback_summary(newsletters)

            # Parse JSON response
            try:
                summary_data: dict[str, Any] = json.loads(ai_response)
                logger.info("AI summarization completed successfully")
                return summary_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI JSON response: {e}")
                logger.debug(f"Raw AI response: {ai_response[:500]}...")
                return self._create_fallback_summary(newsletters)

        except Exception as e:
            logger.error(f"AI API call failed: {e}")
            return self._create_fallback_summary(newsletters)

    def _get_system_prompt(self) -> str:
        """Get the structured system prompt for English newsletter summarization."""
        # Role and Objective
        role_definition = (
            "You are a professional information analyst specializing in consolidating "
            "multiple newsletters into efficient daily summaries. Your goal is to help "
            "busy professionals get 80% of the most important information in 10 minutes."
        )

        # JSON Output Format
        json_format = """{
  "daily_highlights": [
    "3-5 most important key points of the day, each 1-2 sentences with links when available"
  ],
  "categories": {
    "technology": {
      "summary": "Overall summary of technology category developments",
      "priority": "high|medium|low",
      "items": ["Specific items with format: Title ([link](url)) - brief description"]
    },
    "business": {
      "summary": "Overall summary of business and finance developments",
      "priority": "high|medium|low",
      "items": ["Specific items with format: Title ([link](url)) - brief description"]
    },
    "industry_trends": {
      "summary": "Overall summary of industry trends and market insights",
      "priority": "high|medium|low",
      "items": ["Specific items with format: Title ([link](url)) - brief description"]
    },
    "tools_resources": {
      "summary": "Overview of useful tools, resources, and actionable content",
      "priority": "high|medium|low",
      "items": ["Specific items with format: Title ([link](url)) - brief description"]
    }
  },
  "reading_time": "Estimated reading time",
  "meta": {
    "total_sources": "Number of newsletters processed",
    "processing_date": "Processing date"
  }
}"""

        # Processing Principles
        processing_principles = """
Processing Guidelines:
1. Impact Assessment: Focus on high-impact, time-sensitive information
2. Deduplication: Merge similar topics to avoid redundancy
3. Information Density: Keep category summaries to 100-150 words each
4. Actionability: Prioritize practical tools, resources, and links
5. Link Integration: Include original links in format: Title ([link](url))
6. Professional Tone: Clear, concise, business-focused English"""

        return f"{role_definition}\n\nAnalyze the provided newsletter content and output in this JSON format:\n{json_format}\n{processing_principles}"

    def _create_user_prompt(
        self, newsletters: list[NewsletterContent], combined_content: str
    ) -> str:
        """Create structured user prompt for newsletter analysis."""
        # Task Description
        task_description = f"Analyze the following {len(newsletters)} newsletter contents and generate today's summary:"

        # Content Section
        content_section = f"\n{combined_content}\n"

        # Specific Focus Areas
        focus_areas = """
Priority Focus Areas:
- Breaking trends and significant news developments
- Practical tools, resources, and actionable insights
- Major business developments and market movements
- Notable technology breakthroughs and innovations
- Include original article links where available

Target Audience: Technology and business professionals seeking efficient information consumption.
"""

        # Output Requirements
        output_requirements = """
Output Requirements:
- Strict JSON format adherence - ensure all fields contain meaningful content
- Include links in items using format: Title ([link](url)) - description
- Prioritize high-impact, actionable information
- Maintain professional, concise tone"""

        return f"{task_description}{content_section}{focus_areas}{output_requirements}"

    def _create_combined_content(self, newsletters: list[NewsletterContent]) -> str:
        """Combine all newsletter contents with links for AI processing."""
        newsletter_sections = []

        for i, newsletter in enumerate(newsletters, 1):
            # Limit content length to avoid token limits
            content_preview = (
                newsletter.content[:2000]
                if len(newsletter.content) > 2000
                else newsletter.content
            )

            # Include links if available
            links_section = ""
            if newsletter.links:
                links_section = "\nAvailable Links:\n"
                for link in newsletter.links[
                    :10
                ]:  # Limit to 10 links to avoid token overflow
                    links_section += f"- {link}\n"

            section = f"""=== Newsletter {i}: {newsletter.title} ===
Source: {newsletter.source}
Date: {newsletter.date}
Content:
{content_preview}{links_section}
"""
            newsletter_sections.append(section)

        return "\n".join(newsletter_sections)

    def _create_fallback_summary(
        self, newsletters: list[NewsletterContent]
    ) -> dict[str, Any]:
        """Create fallback summary when AI fails."""
        logger.warning("Using fallback summary generation")

        # Simple fallback structure
        highlights = []
        items = []

        for newsletter in newsletters[:5]:  # Limit quantity for performance
            summary = self._fallback_summarize(newsletter.content)
            highlights.append(f"{newsletter.title}: {summary[:100]}...")
            items.append(
                {
                    "title": newsletter.title,
                    "source": newsletter.source,
                    "summary": summary,
                }
            )

        return {
            "daily_highlights": highlights,
            "categories": {
                "general": {
                    "summary": f"Today's digest includes {len(newsletters)} newsletters covering technology, business, and other key domains.",
                    "priority": "high",
                    "items": [item["title"] for item in items],
                }
            },
            "reading_time": "Estimated 8-12 minutes",
            "meta": {
                "total_sources": len(newsletters),
                "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "fallback_mode": True,
            },
        }

    def _fallback_summarize(self, content: str) -> str:
        """Fallback summarization method (character truncation)."""
        max_length = 300

        if len(content) <= max_length:
            return content

        truncated = content[:max_length]
        sentence_endings = [".", "!", "?", "。", "！", "？"]
        best_break = -1

        for i in range(len(truncated) - 1, max(len(truncated) - 50, 0), -1):
            if truncated[i] in sentence_endings and i < len(truncated) - 1:
                if truncated[i] == "." and i > 0 and truncated[i - 1].isupper():
                    continue
                best_break = i + 1
                break

        if best_break > 0:
            return truncated[:best_break].strip() + "..."
        else:
            return truncated.rstrip() + "..."
