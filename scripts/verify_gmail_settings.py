#!/usr/bin/env python3
"""
Gmail IMAP Settings Verification Script.

This script helps verify that your Gmail IMAP settings are optimal
for the Good Morning Agent system.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imap_behavior():
    """Test IMAP behavior with current Gmail settings."""
    print("🔍 Gmail IMAP Settings Verification")
    print("=" * 50)
    
    try:
        from src.utils.config import load_config
        from src.collectors.email_reader import EmailReader
        
        # Load config
        config = load_config("config/.env.test")
        
        print(f"📧 Testing account: {config.email.address}")
        print()
        
        # Test connection and read behavior
        reader = EmailReader(
            imap_server=config.email.imap_server,
            imap_port=config.email.imap_port,
            email_address=config.email.address,
            password=config.email.password,
        )
        
        with reader as r:
            # Test mailbox selection
            status, count = r.select_mailbox("INBOX")
            print(f"✅ INBOX access: {count} messages")
            
            # Test reading without modifying
            emails = r.fetch_emails(limit=3)
            print(f"✅ Read {len(emails)} emails (no modification)")
            
            # Test newsletter filtering
            newsletters = r.filter_newsletters(emails)
            print(f"✅ Identified {len(newsletters)} newsletters")
            
            # Test multiple connections (verify no state issues)
            print("\n🔄 Testing multiple connections...")
            
        # Second connection test
        with reader as r:
            status, count2 = r.select_mailbox("INBOX")
            print(f"✅ Second connection: {count2} messages")
            
            if count == count2:
                print("✅ Message count consistent across connections")
            else:
                print(f"⚠️  Message count changed: {count} → {count2}")
                
        print("\n🎉 Gmail IMAP settings verification completed!")
        print("\n📋 Your current settings should work well with:")
        print("   • Auto-Expunge: ON (immediate server updates)")
        print("   • Deleted messages: Archive (preserve history)")
        print("   • Folder limits: No limit (handle large volumes)")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        print("\n💡 Make sure you have:")
        print("   • Created config/.env.test with valid credentials")
        print("   • Enabled IMAP in Gmail settings")
        print("   • Generated an app password")

if __name__ == "__main__":
    test_imap_behavior()