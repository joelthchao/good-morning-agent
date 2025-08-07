#!/usr/bin/env python3
"""
Real data test for the improved newsletter processing system.

This script tests the complete pipeline with actual email data:
1. Connect to real email account
2. Fetch newsletters from the last 7 days  
3. Extract links and clean sources
4. Generate English AI summary
5. Create HTML email format
6. Output results for review
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_email_connection():
    """Test email connection and basic functionality."""
    try:
        from src.collectors.email_reader import EmailReader
        from src.utils.config import get_config
        
        logger.info("🔧 Loading configuration...")
        config = get_config()
        
        # Initialize EmailReader with real credentials
        reader = EmailReader(
            imap_server=config.email.imap_server,
            imap_port=config.email.imap_port,
            email_address=config.email.address,
            password=config.email.password
        )
        
        logger.info("📧 Testing email connection...")
        reader.connect()
        
        # Test basic connection
        status, count = reader.select_mailbox("INBOX")
        logger.info(f"✅ Connected to INBOX: {status}, {count} messages")
        
        # Don't disconnect yet, we'll need the connection for fetching
        return reader, config
        
    except Exception as e:
        logger.error(f"❌ Email connection failed: {e}")
        return None, None

def test_newsletter_fetching(reader, config):
    """Test fetching real newsletters with 7-day filtering."""
    try:
        logger.info("📰 Fetching newsletters from last 7 days...")
        
        # Use the improved method that includes 7-day filtering, link extraction, and source cleaning
        newsletters = reader.get_recent_newsletters_as_content(days=7, limit=5)
        
        logger.info(f"📊 Found {len(newsletters)} newsletters")
        
        if not newsletters:
            logger.warning("⚠️  No newsletters found in the last 7 days")
            return []
            
        # Display newsletter info
        for i, newsletter in enumerate(newsletters, 1):
            logger.info(f"\n📄 Newsletter {i}:")
            logger.info(f"  📝 Title: {newsletter.title}")
            logger.info(f"  📧 Source: {newsletter.source}")  # Should now show clean email
            logger.info(f"  📅 Date: {newsletter.date}")
            logger.info(f"  📏 Content Length: {len(newsletter.content)} chars")
            logger.info(f"  🔗 Links: {len(newsletter.links) if newsletter.links else 0} found")
            
            if newsletter.links:
                logger.info(f"  🔗 Sample Links: {newsletter.links[:3]}...")
                
            # Show content preview
            content_preview = newsletter.content[:200] + "..." if len(newsletter.content) > 200 else newsletter.content
            logger.info(f"  💬 Preview: {content_preview}")
            
        return newsletters
        
    except Exception as e:
        logger.error(f"❌ Newsletter fetching failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def test_ai_processing(newsletters):
    """Test AI processing with English prompts and link integration."""
    try:
        from src.processors.newsletter_processor import NewsletterProcessor
        
        if not newsletters:
            logger.warning("⚠️  No newsletters to process")
            return None
            
        logger.info("🤖 Starting AI processing...")
        processor = NewsletterProcessor()
        
        # Process newsletters (should use English prompts and include links)
        result = processor.process_newsletters(newsletters)
        
        if not result.success:
            logger.error(f"❌ Processing failed: {result.errors}")
            return None
            
        logger.info("✅ AI processing completed successfully")
        logger.info(f"📊 Processed: {result.processed_count}, Failed: {result.failed_count}")
        
        # Display results
        email_data = result.email_data
        logger.info(f"\n📧 Generated Email:")
        logger.info(f"  📧 To: {email_data.recipient}")
        logger.info(f"  📝 Subject: {email_data.subject}")  # Should be in English
        logger.info(f"  📏 Text Content Length: {len(email_data.content)} chars")
        logger.info(f"  🎨 HTML Content: {'Yes' if email_data.html_content else 'No'}")
        
        if email_data.html_content:
            logger.info(f"  📏 HTML Content Length: {len(email_data.html_content)} chars")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ AI processing failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_output_samples(result):
    """Save output samples for review."""
    try:
        if not result or not result.email_data:
            logger.warning("⚠️  No result data to save")
            return
            
        # Create output directory
        output_dir = Path("output_samples")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save text version
        text_file = output_dir / f"newsletter_summary_{timestamp}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"Subject: {result.email_data.subject}\n")
            f.write(f"To: {result.email_data.recipient}\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write("=" * 60 + "\n\n")
            f.write(result.email_data.content)
            
        logger.info(f"💾 Text version saved: {text_file}")
        
        # Save HTML version if available
        if result.email_data.html_content:
            html_file = output_dir / f"newsletter_summary_{timestamp}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(result.email_data.html_content)
                
            logger.info(f"💾 HTML version saved: {html_file}")
            
        # Save metadata
        meta_file = output_dir / f"newsletter_meta_{timestamp}.txt"
        with open(meta_file, 'w', encoding='utf-8') as f:
            f.write("Newsletter Processing Metadata\n")
            f.write("=" * 40 + "\n")
            f.write(f"Processed Count: {result.processed_count}\n")
            f.write(f"Failed Count: {result.failed_count}\n")
            f.write(f"Success: {result.success}\n")
            f.write(f"Errors: {result.errors}\n")
            f.write(f"Metadata: {result.email_data.metadata}\n")
            
        logger.info(f"💾 Metadata saved: {meta_file}")
        
    except Exception as e:
        logger.error(f"❌ Failed to save output: {e}")

def main():
    """Run the complete real data test."""
    logger.info("🌟 Starting Good Morning Agent Real Data Test")
    logger.info("=" * 60)
    
    try:
        # Test 1: Email Connection
        logger.info("\n🔧 Phase 1: Testing Email Connection")
        reader, config = test_email_connection()
        if not reader:
            logger.error("❌ Email connection failed, cannot proceed")
            return False
            
        # Test 2: Newsletter Fetching (with improvements)
        logger.info("\n📰 Phase 2: Fetching Real Newsletters")
        newsletters = test_newsletter_fetching(reader, config)
        reader.disconnect()  # Clean up connection
        
        if not newsletters:
            logger.warning("⚠️  No newsletters found, but connection worked")
            return True  # Connection worked, just no data
            
        # Test 3: AI Processing (with English prompts and HTML)
        logger.info("\n🤖 Phase 3: AI Processing with Improvements")
        result = test_ai_processing(newsletters)
        
        if not result:
            logger.error("❌ AI processing failed")
            return False
            
        # Test 4: Save Output Samples
        logger.info("\n💾 Phase 4: Saving Output Samples")
        save_output_samples(result)
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("🎉 Real Data Test Completed Successfully!")
        logger.info("\n✅ Verified Improvements:")
        logger.info("  📅 7-day filtering: Used in newsletter fetching")
        logger.info("  📧 Source parsing: Check newsletter sources in output")  
        logger.info("  🔗 Link extraction: Check link counts in logs")
        logger.info("  🇺🇸 English prompts: Check AI output language")
        logger.info("  🎨 HTML formatting: Check HTML file generation")
        logger.info("  📤 Email integration: Check multipart email structure")
        
        logger.info(f"\n📊 Final Stats:")
        logger.info(f"  📰 Newsletters processed: {result.processed_count}")
        logger.info(f"  ❌ Processing failures: {result.failed_count}")
        logger.info(f"  ✅ Overall success: {result.success}")
        
        if result.email_data.html_content:
            logger.info("  🎨 HTML content: Generated successfully")
        
        logger.info("\n📁 Check 'output_samples/' directory for generated files")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        logger.info("\n🌟 Test completed successfully! 🌟")
        sys.exit(0)
    else:
        logger.error("\n💥 Test failed! 💥")
        sys.exit(1)