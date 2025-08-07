"""
HTML formatter for newsletter email content.

This module converts structured summary data into responsive HTML email format.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class HTMLFormatter:
    """Formats email content into HTML messages."""

    def __init__(self) -> None:
        """Initialize the HTML formatter."""
        self.css_styles = self._get_embedded_css()

    def format_html(self, summary_data: dict[str, Any]) -> str:
        """
        Format structured summary data into HTML email.

        Args:
            summary_data: Structured summary data from AI processing

        Returns:
            Complete HTML email content
        """
        try:
            # Build HTML components
            html_header = self._create_html_header()
            email_header = self._create_email_header(summary_data)
            highlights_section = self._create_highlights_section(summary_data)
            categories_section = self._create_categories_section(summary_data)
            footer_section = self._create_footer_section(summary_data)

            # Combine all sections
            html_content = f"""{html_header}
<body>
    <div class="container">
        {email_header}
        {highlights_section}
        {categories_section}
        {footer_section}
    </div>
</body>
</html>"""
            logger.debug(
                f"Generated HTML content length: {len(html_content)} characters"
            )
            return html_content

        except Exception as e:
            logger.error(f"Error formatting HTML content: {e}")
            # Return a basic fallback HTML
            return self._create_fallback_html(summary_data)

    def _get_embedded_css(self) -> str:
        """Get embedded CSS styles for email compatibility."""
        return """
        <style>
            /* Email-safe CSS styles */
            body {
                margin: 0;
                padding: 0;
                font-family: Arial, sans-serif;
                background-color: #f5f5f5;
                line-height: 1.6;
            }
            .container {
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                padding: 20px;
            }
            .header {
                text-align: center;
                border-bottom: 3px solid #2c3e50;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            .header h1 {
                color: #2c3e50;
                font-size: 28px;
                margin: 0;
            }
            .meta-info {
                color: #7f8c8d;
                font-size: 14px;
                margin-top: 10px;
            }
            .section {
                margin-bottom: 30px;
            }
            .section-title {
                color: #2c3e50;
                font-size: 22px;
                font-weight: bold;
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 2px solid #ecf0f1;
            }
            .highlight-item {
                background-color: #f8f9fa;
                padding: 15px;
                margin-bottom: 10px;
                border-left: 4px solid #3498db;
                border-radius: 4px;
            }
            .category {
                background-color: #ffffff;
                border: 1px solid #ecf0f1;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
            }
            .category-header {
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }
            .category-title {
                color: #2c3e50;
                font-size: 18px;
                font-weight: bold;
                margin: 0 10px 0 0;
            }
            .priority-badge {
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                color: white;
            }
            .priority-high { background-color: #e74c3c; }
            .priority-medium { background-color: #f39c12; }
            .priority-low { background-color: #27ae60; }
            .category-summary {
                color: #34495e;
                margin-bottom: 15px;
                line-height: 1.5;
            }
            .items-list {
                padding-left: 0;
                list-style: none;
            }
            .items-list li {
                background-color: #f8f9fa;
                padding: 10px 15px;
                margin-bottom: 8px;
                border-radius: 4px;
                border-left: 3px solid #3498db;
            }
            .items-list a {
                color: #3498db;
                text-decoration: none;
            }
            .items-list a:hover {
                text-decoration: underline;
            }
            .footer {
                background-color: #ecf0f1;
                padding: 20px;
                text-align: center;
                color: #7f8c8d;
                font-size: 14px;
                margin-top: 30px;
                border-radius: 8px;
            }
            .footer-stats {
                margin-bottom: 15px;
            }
            .footer-stats div {
                margin-bottom: 5px;
            }
            /* Responsive design */
            @media only screen and (max-width: 600px) {
                .container {
                    padding: 15px;
                }
                .header h1 {
                    font-size: 24px;
                }
                .section-title {
                    font-size: 20px;
                }
                .category-title {
                    font-size: 16px;
                }
            }
        </style>
        """

    def _create_html_header(self) -> str:
        """Create HTML document header with CSS."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Newsletter Summary</title>
    {self.css_styles}
</head>"""

    def _create_html_footer(self) -> str:
        """Create HTML document footer."""
        return "</html>"

    def _create_email_header(self, summary_data: dict[str, Any]) -> str:
        """Create email header section."""
        current_date = datetime.now().strftime("%Y-%m-%d")
        reading_time = summary_data.get("reading_time", "Estimated 8-12 minutes")
        total_sources = summary_data.get("meta", {}).get("total_sources", "N/A")

        return f"""
        <div class="header">
            <h1>🌅 Daily Newsletter Summary</h1>
            <div class="meta-info">
                <strong>{current_date}</strong><br>
                📖 {reading_time} | 🗂️ {total_sources} newsletters
            </div>
        </div>
        """

    def _create_highlights_section(self, summary_data: dict[str, Any]) -> str:
        """Create daily highlights section."""
        highlights = summary_data.get("daily_highlights", [])
        if not highlights:
            return ""

        highlights_html = (
            '<div class="section"><h2 class="section-title">🎯 Today\'s Highlights</h2>'
        )

        for i, highlight in enumerate(highlights, 1):
            highlights_html += f"""
            <div class="highlight-item">
                <strong>{i}.</strong> {highlight}
            </div>
            """

        highlights_html += "</div>"
        return highlights_html

    def _create_categories_section(self, summary_data: dict[str, Any]) -> str:
        """Create categories breakdown section."""
        categories = summary_data.get("categories", {})
        if not categories:
            return ""

        # Category mappings with emojis
        category_info = {
            "technology": ("🚀", "Technology"),
            "tech_innovation": ("🚀", "Technology"),  # backward compatibility
            "business": ("💰", "Business"),
            "business_finance": ("💰", "Business"),  # backward compatibility
            "industry_trends": ("📈", "Industry Trends"),
            "tools_resources": ("🔧", "Tools & Resources"),
            "general": ("📰", "General"),
        }

        categories_html = (
            '<div class="section"><h2 class="section-title">📂 Category Breakdown</h2>'
        )

        for category_key, category_data in categories.items():
            emoji, display_name = category_info.get(
                category_key, ("📰", category_key.replace("_", " ").title())
            )
            priority = category_data.get("priority", "medium")
            summary = category_data.get("summary", "")
            items = category_data.get("items", [])

            categories_html += f"""
            <div class="category">
                <div class="category-header">
                    <h3 class="category-title">{emoji} {display_name}</h3>
                    <span class="priority-badge priority-{priority}">{priority.upper()}</span>
                </div>
                <div class="category-summary">{summary}</div>
            """

            if items:
                categories_html += '<ul class="items-list">'
                for item in items[:5]:  # Limit to 5 items
                    # Parse item for links (format: Title ([link](url)) - description)
                    formatted_item = self._format_item_with_links(item)
                    categories_html += f"<li>{formatted_item}</li>"
                categories_html += "</ul>"

            categories_html += "</div>"

        categories_html += "</div>"
        return categories_html

    def _format_item_with_links(self, item: str) -> str:
        """Format item text to convert markdown links to HTML."""
        import re

        # Convert markdown links [text](url) to HTML <a> tags
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        formatted_item = re.sub(
            link_pattern, r'<a href="\2" target="_blank">\1</a>', item
        )

        return formatted_item

    def _create_footer_section(self, summary_data: dict[str, Any]) -> str:
        """Create footer section with statistics."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_sources = summary_data.get("meta", {}).get("total_sources", "N/A")
        ai_mode = (
            "Normal"
            if not summary_data.get("meta", {}).get("fallback_mode")
            else "Fallback"
        )

        return f"""
        <div class="footer">
            <div class="footer-stats">
                <div><strong>📊 Processing Summary</strong></div>
                <div>Sources: {total_sources} newsletters</div>
                <div>Processing Time: {current_time}</div>
                <div>AI Mode: {ai_mode}</div>
            </div>
            <div>
                🤖 This summary was automatically generated by Good Morning Agent using AI technology
            </div>
        </div>
        """

    def _create_fallback_html(self, summary_data: dict[str, Any]) -> str:
        """Create basic fallback HTML when main formatting fails."""
        current_date = datetime.now().strftime("%Y-%m-%d")

        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Daily Newsletter Summary</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🌅 Daily Newsletter Summary - {current_date}</h1>
        <p>Generated summary for today's newsletters.</p>
        <p>📊 Processing Summary: {summary_data.get('meta', {}).get('total_sources', 'N/A')} newsletters processed</p>
        <p><em>🤖 Generated by Good Morning Agent</em></p>
    </div>
</body>
</html>
        """
