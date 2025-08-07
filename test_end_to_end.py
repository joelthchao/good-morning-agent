#!/usr/bin/env python3
"""
End-to-End Test Script for Good Morning Agent
Tests the complete pipeline: Email Collection → AI Processing → Email Sending
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.utils.config import get_config
from src.collectors.email_reader import EmailReader
from src.processors.newsletter_processor import NewsletterProcessor
from src.senders.email_sender import EmailSender
from src.senders.models import EmailData
from src.senders.html_formatter import HTMLFormatter


def test_end_to_end(send_email: bool = False, limit: int = 10, days: int = 7):
    """Execute complete end-to-end test with actual email sending"""
    print("🚀 Starting End-to-End Test")
    print("=" * 50)
    
    try:
        # Load configuration
        print("📁 Loading configuration...")
        config = get_config()
        
        # Initialize components
        print("🔧 Initializing components...")
        email_reader = EmailReader(
            imap_server=config.email.imap_server,
            imap_port=config.email.imap_port,
            email_address=config.email.address,
            password=config.email.password
        )
        processor = NewsletterProcessor()
        email_sender = EmailSender(config.email)
        html_formatter = HTMLFormatter()
        
        # Step 1: Connect and collect newsletters
        print("\n📧 Step 1: Connecting to email server...")
        email_reader.connect()
        
        print(f"📧 Collecting newsletters ({days} days, limit {limit})...")
        newsletters = email_reader.get_recent_newsletters_as_content(days=days, limit=limit)
        print(f"✅ Found {len(newsletters)} newsletters to process")
        
        if not newsletters:
            print(f"⚠️  No newsletters found in the last {days} days")
            return
        
        # Display newsletter sources
        for i, newsletter in enumerate(newsletters, 1):
            print(f"  {i}. {newsletter.source} - {newsletter.title[:60]}...")
        
        # Step 2: Process with AI
        print(f"\n🤖 Step 2: Processing {len(newsletters)} newsletters with AI...")
        processing_result = processor.process_newsletters(newsletters)
        
        if not processing_result.success:
            print(f"❌ Failed to process newsletters: {processing_result.errors}")
            return
        
        print("✅ AI processing completed successfully")
        print(f"  - Processed: {processing_result.processed_count}")
        print(f"  - Failed: {processing_result.failed_count}")
        
        # Get email data from processing result
        email_data = processing_result.email_data
        print(f"  - Subject: {email_data.subject}")
        print(f"  - Content length: {len(email_data.content)} characters")
        
        # HTML content is already in email_data
        html_content = email_data.html_content
        if html_content:
            print(f"  - HTML content: {len(html_content)} characters")
        else:
            print("  - No HTML content generated")
        
        # Step 3: Email is already prepared by processor
        print("\n✉️  Step 3: Email data ready for sending...")
        
        print(f"✅ Email prepared for: {email_data.recipient}")
        print(f"  - Subject: {email_data.subject}")
        print(f"  - Plain text: {len(email_data.content)} characters")
        if html_content:
            print(f"  - HTML content: {len(html_content)} characters")
        
        # Step 4: Send email or save to file
        if send_email:
            print("\n📤 Step 4: Sending email...")
            print(f"⚠️  Sending email to: {email_data.recipient}")
            success = email_sender.send_email(email_data)
            if success:
                print("✅ Email sent successfully!")
                print(f"📧 Check your inbox at: {email_data.recipient}")
            else:
                print("❌ Failed to send email")
                return
        else:
            print("\n💾 Step 4: Saving content to file for review...")
            
            # Save to output files
            output_dir = Path("output_samples")
            output_dir.mkdir(exist_ok=True)
            
            current_date = datetime.now()
            timestamp = current_date.strftime("%Y%m%d_%H%M%S")
            
            # Save HTML if available
            if html_content:
                html_file = output_dir / f"end_to_end_test_{timestamp}.html"
                html_file.write_text(html_content, encoding='utf-8')
                print(f"✅ HTML saved: {html_file}")
            
            # Save plain text
            txt_file = output_dir / f"end_to_end_test_{timestamp}.txt"
            txt_file.write_text(email_data.content, encoding='utf-8')
            print(f"✅ Text saved: {txt_file}")
            
            print("💡 To actually send email, run: uv run python test_end_to_end.py --send")
        
        print("\n🎉 End-to-End Test Complete!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error in end-to-end test: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up connections
        try:
            email_reader.disconnect()
        except:
            pass


def main():
    """Main function with argument parsing."""
    parser = argparse.ArgumentParser(
        description="End-to-End test for Good Morning Agent newsletter processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_end_to_end.py           # Test and save to file
  python test_end_to_end.py --send    # Test and actually send email
  uv run python test_end_to_end.py --send
        """
    )
    
    parser.add_argument(
        "--send",
        action="store_true",
        help="Actually send the email (default: save to file only)"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of newsletters to process (default: 10)"
    )
    
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back for newsletters (default: 7)"
    )
    
    args = parser.parse_args()
    
    print(f"🔧 Configuration:")
    print(f"  - Send email: {'Yes' if args.send else 'No (save to file only)'}")
    print(f"  - Newsletter limit: {args.limit}")
    print(f"  - Days lookback: {args.days}")
    print()
    
    test_end_to_end(send_email=args.send, limit=args.limit, days=args.days)


if __name__ == "__main__":
    main()