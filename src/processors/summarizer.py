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
        """Get the system prompt for AI summarization."""
        return """你是專業的資訊分析師，專門將多份電子報整合成高效的每日摘要。你的目標是幫助忙碌的用戶在 10 分鐘內獲得 80% 最重要的資訊。

請分析提供的電子報內容，並按以下 JSON 格式輸出：
{
  "daily_highlights": [
    "今日最重要的 3-5 個關鍵要點，每個要點 1-2 句話"
  ],
  "categories": {
    "tech_innovation": {
      "summary": "科技創新類別的整體摘要",
      "priority": "high|medium|low",
      "items": ["具體項目列表"]
    },
    "business_finance": {
      "summary": "商業金融類別的整體摘要",
      "priority": "high|medium|low",
      "items": ["具體項目列表"]
    },
    "industry_trends": {
      "summary": "產業趨勢類別的整體摘要",
      "priority": "high|medium|low",
      "items": ["具體項目列表"]
    },
    "tools_resources": {
      "summary": "工具資源類別的整體摘要",
      "priority": "high|medium|low",
      "items": ["具體項目列表"]
    }
  },
  "reading_time": "預估閱讀時間",
  "meta": {
    "total_sources": "處理的電子報數量",
    "processing_date": "處理日期"
  }
}

處理原則：
1. 重要性評估：關注影響範圍大、時效性強的資訊
2. 去重整合：相同主題的內容要合併，避免重複
3. 資訊密度：每個類別摘要控制在 100-150 字
4. 可操作性：優先提及實用工具、資源連結
5. 繁體中文輸出，專業但易讀的語調"""

    def _create_user_prompt(
        self, newsletters: list[NewsletterContent], combined_content: str
    ) -> str:
        """Create user prompt for AI processing."""
        return f"""請分析以下 {len(newsletters)} 份電子報內容，生成今日摘要：

{combined_content}

請嚴格按照 JSON 格式輸出，確保所有字段都包含有意義的內容。重點關注：
- 今日最重要的趨勢和新聞
- 實用的工具和資源
- 影響較大的商業動態
- 值得關注的技術突破

目標讀者：關注科技和商業趨勢的專業人士，希望快速掌握重點資訊。"""

    def _create_combined_content(self, newsletters: list[NewsletterContent]) -> str:
        """Combine all newsletter contents for AI processing."""
        newsletter_sections = []

        for i, newsletter in enumerate(newsletters, 1):
            # 限制每個電子報的內容長度避免超出 token 限制
            content_preview = (
                newsletter.content[:2000]
                if len(newsletter.content) > 2000
                else newsletter.content
            )

            section = f"""=== 電子報 {i}: {newsletter.title} ===
來源: {newsletter.source}
日期: {newsletter.date}
內容:
{content_preview}
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

        for newsletter in newsletters[:5]:  # 限制數量
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
                    "summary": f"今日收集了 {len(newsletters)} 份電子報，涵蓋科技、商業等多個領域的重要資訊。",
                    "priority": "high",
                    "items": [item["title"] for item in items],
                }
            },
            "reading_time": "預估 8-12 分鐘",
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
