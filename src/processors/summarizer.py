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
from src.utils.config import Config

logger = logging.getLogger(__name__)


class Summarizer:
    """AI-powered content summarizer using OpenAI API."""

    def __init__(self, config: Config) -> None:
        """Initialize the summarizer with OpenAI client."""
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
        Automatically handles batch processing if content exceeds token limits.

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

        # Check if we need batch processing
        estimated_tokens = self._estimate_batch_tokens(newsletters)
        logger.info(f"Estimated tokens: {estimated_tokens}")

        # If tokens are within limit, process normally
        if estimated_tokens <= 12000:
            logger.info("Processing all newsletters in single batch")
            return self._process_single_batch(newsletters)

        # Otherwise, use batch processing
        logger.info("Content exceeds token limit, using batch processing")
        return self._process_in_batches(newsletters)

    def _process_single_batch(
        self, newsletters: list[NewsletterContent]
    ) -> dict[str, Any]:
        """Process newsletters in a single API call."""
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

    def _process_in_batches(
        self, newsletters: list[NewsletterContent]
    ) -> dict[str, Any]:
        """Process newsletters in multiple batches and combine results."""
        try:
            # Split into smaller batches (3-4 newsletters per batch)
            batch_size = 3
            batches = [
                newsletters[i : i + batch_size]
                for i in range(0, len(newsletters), batch_size)
            ]

            logger.info(
                f"Processing {len(newsletters)} newsletters in {len(batches)} batches"
            )

            batch_summaries = []

            # Process each batch
            for i, batch in enumerate(batches, 1):
                logger.info(
                    f"Processing batch {i}/{len(batches)} with {len(batch)} newsletters"
                )

                try:
                    batch_summary = self._process_single_batch(batch)
                    batch_summaries.append(batch_summary)
                except Exception as e:
                    logger.warning(
                        f"Batch {i} failed: {e}, continuing with remaining batches"
                    )
                    continue

            if not batch_summaries:
                logger.error("All batches failed, using fallback")
                return self._create_fallback_summary(newsletters)

            # Combine batch summaries into final result
            return self._combine_batch_summaries(batch_summaries, len(newsletters))

        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return self._create_fallback_summary(newsletters)

    def _combine_batch_summaries(
        self, batch_summaries: list[dict[str, Any]], total_newsletters: int
    ) -> dict[str, Any]:
        """Combine multiple batch summaries into a single comprehensive summary."""
        # Collect all highlights
        all_highlights = []
        for batch in batch_summaries:
            highlights = batch.get("daily_highlights", [])
            all_highlights.extend(highlights)

        # Combine categories
        combined_categories = {}
        category_types = [
            "technology",
            "business",
            "industry_trends",
            "tools_resources",
        ]

        for category in category_types:
            items = []
            summaries = []
            highest_priority = "low"

            for batch in batch_summaries:
                batch_category = batch.get("categories", {}).get(category, {})
                if batch_category:
                    items.extend(batch_category.get("items", []))
                    if batch_category.get("summary"):
                        summaries.append(batch_category["summary"])

                    # Get highest priority
                    priority = batch_category.get("priority", "low")
                    if priority == "high" or highest_priority == "low":
                        highest_priority = priority

            if items or summaries:
                combined_categories[category] = {
                    "summary": (
                        " ".join(summaries[:2])
                        if summaries
                        else f"Combined insights from multiple newsletters in {category}"
                    ),
                    "priority": highest_priority,
                    "items": items[:8],  # Limit to prevent overflow
                }

        # Create final summary
        return {
            "daily_highlights": all_highlights[:5],  # Top 5 highlights
            "categories": combined_categories,
            "reading_time": f"Estimated {8 + len(batch_summaries) * 2}-{12 + len(batch_summaries) * 3} minutes",
            "meta": {
                "total_sources": total_newsletters,
                "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "batch_processed": True,
                "batch_count": len(batch_summaries),
            },
        }

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

    def _clean_newsletter_content(self, content: str) -> str:
        """Clean newsletter content to reduce token usage."""
        if not content:
            return ""

        import re

        # Remove HTML tags but keep text content
        content = re.sub(r"<[^>]+>", " ", content)

        # Remove email headers (lines starting with common email prefixes)
        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            # Skip email headers and metadata lines
            if (
                line.startswith(">")
                or line.startswith("From:")
                or line.startswith("To:")
                or line.startswith("Subject:")
                or line.startswith("Date:")
                or line.startswith("Reply-To:")
                or line.startswith("Unsubscribe")
                or "unsubscribe" in line.lower()
                and len(line) < 100
            ):
                continue

            # Skip empty lines and very short lines
            if len(line) > 10:
                cleaned_lines.append(line)

        # Join lines and remove multiple spaces
        cleaned_content = " ".join(cleaned_lines)
        cleaned_content = re.sub(r"\s+", " ", cleaned_content)

        # Limit to 1500 characters to reduce token usage
        if len(cleaned_content) > 1500:
            cleaned_content = cleaned_content[:1500]

        return cleaned_content.strip()

    def _estimate_batch_tokens(self, newsletters: list[NewsletterContent]) -> int:
        """Estimate total tokens for a batch of newsletters."""
        total_chars = 0

        # Estimate system prompt tokens (~1000)
        base_tokens = 1000

        for newsletter in newsletters:
            # Clean content and estimate
            cleaned_content = self._clean_newsletter_content(newsletter.content)

            # Add title, source, and content character counts
            total_chars += (
                len(newsletter.title) + len(newsletter.source) + len(cleaned_content)
            )

            # Add links if available (limited estimation)
            if newsletter.links:
                links_chars = sum(
                    len(link) for link in newsletter.links[:5]
                )  # Limit to 5 links
                total_chars += links_chars

        # Convert characters to tokens (rough estimation: 4 chars = 1 token)
        estimated_tokens = base_tokens + (total_chars // 4)

        return estimated_tokens

    def _create_combined_content(self, newsletters: list[NewsletterContent]) -> str:
        """Combine newsletter contents with cleaning for AI processing."""
        newsletter_sections = []

        for i, newsletter in enumerate(newsletters, 1):
            # Use cleaned content
            cleaned_content = self._clean_newsletter_content(newsletter.content)

            # Include limited links if available
            links_section = ""
            if newsletter.links:
                links_section = "\nKey Links:\n"
                for link in newsletter.links[:5]:  # Reduced to 5 links
                    links_section += f"- {link}\n"

            section = f"""=== Newsletter {i}: {newsletter.title} ===
Source: {newsletter.source}
Content: {cleaned_content}{links_section}
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
