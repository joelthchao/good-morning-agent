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
from src.senders.models import EmailData
from src.utils.config import get_config

logger = logging.getLogger(__name__)


class NewsletterProcessor:
    """Main processor for converting newsletters to email format."""

    def __init__(self) -> None:
        """Initialize processor with dependencies."""
        self.summarizer = Summarizer()
        self.error_tracker = ErrorTracker()
        logger.debug("NewsletterProcessor initialized")

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

            # Create final email content from structured summary
            final_content = self._create_structured_content(summary_data)

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

        # Get configuration for recipient
        try:
            config = get_config()
            recipient = config.email.recipient_email or "default@example.com"
        except Exception as e:
            logger.error(f"Failed to get recipient config: {e}")
            recipient = "default@example.com"  # Fallback

        # Create a friendly date for subject
        try:
            from datetime import datetime

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

        # Create EmailData
        email_data = EmailData(
            recipient=recipient,
            subject=f"📧 每日電子報摘要 - {friendly_date}",
            content=final_content,
            metadata=self._create_metadata(
                newsletters[0].date, processed_sources, processed_count, failed_count
            ),
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
🌅 每日智能摘要 - {datetime.now().strftime("%Y-%m-%d")}

📖 {summary_data.get('reading_time', '預估 8-12 分鐘')} | 🗂️ {summary_data.get('meta', {}).get('total_sources', 'N/A')} 份電子報

{'=' * 60}
"""

        # Daily highlights section
        highlights_content = "\n🎯 今日重點\n\n"
        for i, highlight in enumerate(summary_data.get("daily_highlights", []), 1):
            highlights_content += f"{i}. {highlight}\n"
        highlights_content += f"\n{'=' * 60}\n"

        # Categories section
        categories_content = "\n📂 分類摘要\n\n"
        categories = summary_data.get("categories", {})

        # Define category emojis and Chinese names
        category_info = {
            "tech_innovation": ("🚀", "科技創新"),
            "business_finance": ("💰", "商業金融"),
            "industry_trends": ("📈", "產業趨勢"),
            "tools_resources": ("🔧", "工具資源"),
            "general": ("📰", "綜合資訊"),  # fallback category
        }

        for category_key, category_data in categories.items():
            emoji, chinese_name = category_info.get(category_key, ("📰", category_key))
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                category_data.get("priority", "medium"), "🟡"
            )

            categories_content += f"{emoji} {chinese_name} {priority_emoji}\n"
            categories_content += f"{category_data.get('summary', '')}\n\n"

            # Add items if available
            if category_data.get("items"):
                categories_content += "重點項目：\n"
                for item in category_data["items"][:5]:  # 限制顯示數量
                    categories_content += f"• {item}\n"
                categories_content += "\n"

            categories_content += f"{'─' * 40}\n\n"

        # Footer
        footer = f"""
📊 處理統計
• 來源數量：{summary_data.get('meta', {}).get('total_sources', 'N/A')} 份電子報
• 處理時間：{current_time}
• AI 模式：{'正常' if not summary_data.get('meta', {}).get('fallback_mode') else '備用模式'}

🤖 此摘要由 Good Morning Agent 使用 AI 技術自動生成
"""

        return header + highlights_content + categories_content + footer

    def _combine_content(self, sections: list[str]) -> str:
        """Combine multiple newsletter sections into final content (fallback method)."""
        header = f"""
📧 每日電子報摘要

本日共收集 {len(sections)} 份電子報，以下是摘要內容：

{'=' * 50}
"""

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer = f"""
📊 摘要統計
• 處理電子報數量：{len(sections)}
• 生成時間：{current_time}

此摘要由 Good Morning Agent 自動生成。
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
