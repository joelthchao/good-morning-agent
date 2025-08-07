"""
Main newsletter processor for Good Morning Agent.

This module handles the core processing logic, converting newsletter content
into formatted emails ready for sending.
"""

import logging
from datetime import datetime
from typing import Any

from src.processors.error_tracker import ErrorTracker
from src.processors.models import NewsletterContent, ProcessingResult
from src.processors.summarizer import Summarizer
from src.senders.html_formatter import HTMLFormatter
from src.senders.models import EmailData
from src.utils.config import get_config

logger = logging.getLogger(__name__)


class NewsletterProcessor:
    """Main processor for converting newsletters to email format."""

    def __init__(self) -> None:
        """Initialize processor with dependencies."""
        self.summarizer = Summarizer()
        self.error_tracker = ErrorTracker()
        self.html_formatter = HTMLFormatter()
        logger.debug("NewsletterProcessor initialized with HTML support")

    def process_newsletters(
        self, newsletters: list[NewsletterContent]
    ) -> ProcessingResult:
        """
        Process multiple newsletters into a single summary email.

        Args:
            newsletters: List of newsletter content to process

        Returns:
            ProcessingResult containing EmailData or error information
        """
        if not newsletters:
            logger.warning("No newsletters provided for processing")
            return ProcessingResult(
                success=False,
                errors=["No newsletters to process"],
                processed_count=0,
                failed_count=0,
            )

        processed_count = len(newsletters)
        failed_count = 0
        errors = []

        try:
            # Use AI to summarize all newsletters at once
            summary_data = self.summarizer.summarize_newsletters(newsletters)

            # Create final email content from structured summary (both text and HTML)
            final_content = self._create_structured_content(summary_data)
            html_content = self.html_formatter.format_html(summary_data)

            # Get processed sources
            processed_sources = [newsletter.source for newsletter in newsletters]

            logger.info(
                f"Successfully processed {processed_count} newsletters using AI"
            )

        except Exception as e:
            # Record error and use individual processing as fallback
            self.error_tracker.record_error("AI_BATCH_PROCESSING", e)
            errors.append(f"AI batch processing failed: {str(e)}, using fallback")
            logger.error(
                f"AI batch processing failed: {e}, falling back to individual processing"
            )

            # Fallback: process each newsletter individually
            processed_content = []
            processed_sources = []
            processed_count = 0
            failed_count = 0

            for newsletter in newsletters:
                try:
                    # Summarize content individually
                    summary = self.summarizer.summarize(newsletter.content)

                    # Format newsletter section
                    formatted_section = self._format_newsletter_section(
                        newsletter.title, summary, newsletter.source
                    )

                    processed_content.append(formatted_section)
                    processed_sources.append(newsletter.source)
                    processed_count += 1

                    logger.debug(f"Successfully processed: {newsletter.title}")

                except Exception as individual_error:
                    # Record error and continue with other newsletters
                    self.error_tracker.record_error(newsletter.title, individual_error)
                    errors.append(
                        f"Failed to process '{newsletter.title}': {str(individual_error)}"
                    )
                    failed_count += 1

                    logger.error(
                        f"Failed to process '{newsletter.title}': {individual_error}"
                    )

            # Check if we have any successful processing
            if processed_count == 0:
                return ProcessingResult(
                    success=False,
                    errors=errors,
                    processed_count=processed_count,
                    failed_count=failed_count,
                )

            # Create final email content from individual summaries
            final_content = self._combine_content(processed_content)
            # Create basic HTML for fallback mode
            fallback_summary_data = {
                "daily_highlights": [f"Processed {processed_count} newsletters today"],
                "categories": {
                    "general": {
                        "summary": f"Today's digest includes {processed_count} newsletters with individual summaries.",
                        "priority": "medium",
                        "items": [],
                    }
                },
                "reading_time": "Estimated 10-15 minutes",
                "meta": {
                    "total_sources": processed_count,
                    "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "fallback_mode": True,
                },
            }
            html_content = self.html_formatter.format_html(fallback_summary_data)

        # Get configuration for recipient
        try:
            config = get_config()
            recipient = config.email.recipient_email or "default@example.com"
        except Exception as e:
            logger.error(f"Failed to get recipient config: {e}")
            recipient = "default@example.com"  # Fallback

        # Create a friendly date for subject
        try:

            # Try to parse the date and format it nicely
            date_str = newsletters[0].date
            if date_str:
                # Handle common email date formats
                try:
                    parsed_date = datetime.strptime(
                        date_str.split(" +")[0], "%a, %d %b %Y %H:%M:%S"
                    )
                    friendly_date = parsed_date.strftime("%Y-%m-%d")
                except (ValueError, AttributeError):
                    friendly_date = datetime.now().strftime("%Y-%m-%d")
            else:
                friendly_date = datetime.now().strftime("%Y-%m-%d")
        except Exception:
            friendly_date = datetime.now().strftime("%Y-%m-%d")

        # Create EmailData with HTML support
        email_data = EmailData(
            recipient=recipient,
            subject=f"📧 Daily Newsletter Summary - {friendly_date}",
            content=final_content,
            metadata=self._create_metadata(
                newsletters[0].date, processed_sources, processed_count, failed_count
            ),
            html_content=html_content if "html_content" in locals() else None,
        )

        logger.info(
            f"Successfully processed {processed_count} newsletters, {failed_count} failed"
        )

        return ProcessingResult(
            success=True,
            email_data=email_data,
            errors=errors,
            processed_count=processed_count,
            failed_count=failed_count,
        )

    def _format_newsletter_section(self, title: str, content: str, source: str) -> str:
        """Format a single newsletter into a section."""
        return f"""
📰 {title}
來源：{source}

{content}

{'=' * 50}
"""

    def _create_structured_content(self, summary_data: dict) -> str:
        """Create structured email content from AI summary data."""
        # Header
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = f"""
🌅 Daily Newsletter Summary - {datetime.now().strftime("%Y-%m-%d")}

📖 {summary_data.get('reading_time', 'Estimated 8-12 minutes')} | 🗂️ {summary_data.get('meta', {}).get('total_sources', 'N/A')} newsletters

{'=' * 60}
"""

        # Daily highlights section
        highlights_content = "\n🎯 Today's Highlights\n\n"
        for i, highlight in enumerate(summary_data.get("daily_highlights", []), 1):
            highlights_content += f"{i}. {highlight}\n"
        highlights_content += f"\n{'=' * 60}\n"

        # Categories section
        categories_content = "\n📂 Category Breakdown\n\n"
        categories = summary_data.get("categories", {})

        # Define category emojis and English names
        category_info = {
            "technology": ("🚀", "Technology"),
            "tech_innovation": ("🚀", "Technology"),  # backward compatibility
            "business": ("💰", "Business"),
            "business_finance": ("💰", "Business"),  # backward compatibility
            "industry_trends": ("📈", "Industry Trends"),
            "tools_resources": ("🔧", "Tools & Resources"),
            "general": ("📰", "General"),  # fallback category
        }

        for category_key, category_data in categories.items():
            emoji, english_name = category_info.get(category_key, ("📰", category_key))
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                category_data.get("priority", "medium"), "🟡"
            )

            categories_content += f"{emoji} {english_name} {priority_emoji}\n"
            categories_content += f"{category_data.get('summary', '')}\n\n"

            # Add items if available
            if category_data.get("items"):
                categories_content += "Key Items:\n"
                for item in category_data["items"][:5]:  # Limit display quantity
                    categories_content += f"• {item}\n"
                categories_content += "\n"

            categories_content += f"{'─' * 40}\n\n"

        # Footer
        footer = f"""
📊 Processing Summary
• Sources: {summary_data.get('meta', {}).get('total_sources', 'N/A')} newsletters
• Processing Time: {current_time}
• AI Mode: {'Normal' if not summary_data.get('meta', {}).get('fallback_mode') else 'Fallback'}

🤖 This summary was automatically generated by Good Morning Agent using AI technology
"""

        return header + highlights_content + categories_content + footer

    def _combine_content(self, sections: list[str]) -> str:
        """Combine multiple newsletter sections into final content (fallback method)."""
        header = f"""
📧 Daily Newsletter Summary

Today's digest includes {len(sections)} newsletters with the following summaries:

{'=' * 50}
"""

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer = f"""
📊 Summary Statistics
• Processed newsletters: {len(sections)}
• Generated at: {current_time}

This summary was automatically generated by Good Morning Agent.
"""

        return header + "\n".join(sections) + footer

    def _create_metadata(
        self, date: str, sources: list[str], processed_count: int, failed_count: int
    ) -> dict[str, Any]:
        """Create metadata for the email."""
        return {
            "date": date,
            "sources": sources,
            "processed_count": processed_count,
            "failed_count": failed_count,
            "processor_version": "1.0.0",
        }
