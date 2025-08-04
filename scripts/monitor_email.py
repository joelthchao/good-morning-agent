#!/usr/bin/env python3
"""
Real-time Email Monitor for Testing.

This script continuously monitors the test Gmail account for new emails
and displays detailed parsing results for testing purposes.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ruff: noqa: E402
from src.utils.config import load_config
from src.collectors.email_reader import EmailReader


def monitor_emails():
    """Monitor emails in real-time."""
    print("📧 Real-time Email Monitor")
    print("=" * 40)
    print("Waiting for new emails... (Press Ctrl+C to stop)")
    print()

    config = load_config("config/.env.test")

    reader = EmailReader(
        imap_server=config.email.imap_server,
        imap_port=config.email.imap_port,
        email_address=config.email.address,
        password=config.email.password,
    )

    last_count = 0

    try:
        while True:
            with reader as r:
                status, current_count = r.select_mailbox("INBOX")

                if current_count > last_count:
                    print(f"🆕 New email detected! Total: {current_count}")

                    # Fetch the latest email
                    emails = r.fetch_emails(limit=1)

                    if emails:
                        email = emails[0]
                        print("\n📨 Latest Email Details:")
                        print(f"   Subject: {email['subject']}")
                        print(f"   From: {email['sender']}")
                        print(f"   Date: {email['date']}")
                        print(
                            f"   Content Type: {email.get('content_type', 'unknown')}"
                        )
                        print(f"   Is Newsletter: {email.get('is_newsletter', False)}")
                        if email.get("is_newsletter"):
                            print(
                                f"   Newsletter Type: {email.get('newsletter_type', 'unknown')}"
                            )

                        # Show content preview
                        text_content = email.get("text_content", "")
                        if text_content:
                            preview = text_content[:200].replace("\n", " ").strip()
                            print(f"   Content Preview: {preview}...")

                        print("\n" + "─" * 50)

                    last_count = current_count

                elif current_count == last_count and last_count > 0:
                    print(f"📊 Current status: {current_count} emails (no change)")
                else:
                    print(f"📊 Current status: {current_count} emails")

            # Wait 10 seconds before next check
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Error during monitoring: {e}")


def test_latest_email():
    """Test the latest email in detail."""
    print("🔍 Detailed Email Analysis")
    print("=" * 30)

    config = load_config("config/.env.test")

    reader = EmailReader(
        imap_server=config.email.imap_server,
        imap_port=config.email.imap_port,
        email_address=config.email.address,
        password=config.email.password,
    )

    with reader as r:
        status, count = r.select_mailbox("INBOX")
        print(f"📨 Total emails in inbox: {count}")

        if count == 0:
            print("⚠️  No emails found to analyze")
            return

        # Get the latest email
        emails = r.fetch_emails(limit=1)

        if not emails:
            print("❌ Failed to fetch latest email")
            return

        email = emails[0]

        print("\n📧 Email Analysis Results:")
        print("─" * 40)

        # Basic info
        print(f"📎 UID: {email['uid']}")
        print(f"📋 Subject: {email['subject']}")
        print(f"👤 From: {email['sender']}")
        print(f"📅 Date: {email['date']}")
        print(f"🔤 Content Type: {email.get('content_type', 'unknown')}")

        # Newsletter analysis
        print("\n📰 Newsletter Analysis:")
        print(f"   Is Newsletter: {email.get('is_newsletter', False)}")
        if email.get("is_newsletter"):
            print(f"   Newsletter Type: {email.get('newsletter_type', 'unknown')}")

        # Content analysis
        print("\n📝 Content Analysis:")
        text_content = email.get("text_content", "")
        html_content = email.get("html_content", "")

        print(f"   Text Content Length: {len(text_content)} chars")
        print(f"   HTML Content Length: {len(html_content)} chars")

        if text_content:
            print("\n📄 Text Content Preview (first 300 chars):")
            print("─" * 30)
            preview = text_content[:300]
            print(preview)
            if len(text_content) > 300:
                print("... (truncated)")

        if html_content and len(html_content) < 1000:
            print("\n🌐 HTML Content:")
            print("─" * 20)
            print(html_content[:500])
            if len(html_content) > 500:
                print("... (truncated)")


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--analyze":
        test_latest_email()
    else:
        monitor_emails()


if __name__ == "__main__":
    main()
