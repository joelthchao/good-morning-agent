"""
Real Email Integration Tests for EmailReader.

These tests use actual email accounts and require real credentials.
Run with: pytest tests/integration/test_real_email_integration.py -v

Prerequisites:
1. Create a test Gmail account
2. Enable IMAP access
3. Generate app-specific password
4. Copy config/.env.test.example to config/.env.test
5. Fill in your real test credentials
6. Set RUN_INTEGRATION_TESTS=true in your .env.test file
"""

import logging
import pytest
from datetime import datetime, timedelta
from pathlib import Path

from src.collectors.email_reader import EmailReader, EmailConnectionError
from src.utils.config import load_config, validate_config, ConfigurationError


logger = logging.getLogger(__name__)


class TestRealEmailIntegration:
    """Integration tests using real email accounts."""
    
    @pytest.fixture(scope="class")
    def config(self):
        """Load and validate configuration for testing."""
        try:
            config = load_config("config/.env.test")
            validate_config(config)
            return config
        except (ConfigurationError, FileNotFoundError) as e:
            pytest.skip(f"Test configuration not available: {e}")
    
    @pytest.fixture(scope="class") 
    def skip_if_no_integration_tests(self, config):
        """Skip tests if integration testing is disabled."""
        if not config.testing.run_integration_tests:
            pytest.skip("Integration tests disabled. Set RUN_INTEGRATION_TESTS=true in .env.test")
    
    @pytest.fixture
    def email_reader(self, config, skip_if_no_integration_tests):
        """Create EmailReader with real credentials."""
        return EmailReader(
            imap_server=config.email.imap_server,
            imap_port=config.email.imap_port,
            email_address=config.email.address,
            password=config.email.password,
            max_retries=2,  # Reduced for faster testing
            retry_delay=1.0,
        )
    
    def test_real_imap_connection(self, email_reader):
        """Test actual IMAP connection with real credentials."""
        logger.info("Testing real IMAP connection...")
        
        # Test connection using context manager
        with email_reader as reader:
            assert reader.connection is not None
            logger.info("✅ Successfully connected to IMAP server")
            
            # Test mailbox selection
            status, count = reader.select_mailbox("INBOX")
            assert status == "OK"
            assert count >= 0
            logger.info(f"✅ Successfully selected INBOX with {count} messages")
    
    def test_real_imap_connection_failure(self, config):
        """Test IMAP connection failure with invalid credentials."""
        logger.info("Testing IMAP connection failure...")
        
        # Create reader with invalid password
        invalid_reader = EmailReader(
            imap_server=config.email.imap_server,
            imap_port=config.email.imap_port,
            email_address=config.email.address,
            password="invalid_password",
            max_retries=1,
            retry_delay=0.5,
        )
        
        # Should raise EmailConnectionError
        with pytest.raises(EmailConnectionError):
            invalid_reader.connect()
        
        logger.info("✅ Correctly handled invalid credentials")
    
    def test_search_real_emails(self, email_reader):
        """Test searching for real emails in the account."""
        logger.info("Testing email search...")
        
        with email_reader as reader:
            reader.select_mailbox("INBOX")
            
            # Search all emails
            all_uids = reader.search_emails()
            logger.info(f"Found {len(all_uids)} total emails")
            
            # Search recent emails (last 7 days)
            recent_date = datetime.now() - timedelta(days=7)
            recent_uids = reader.search_emails(since_date=recent_date)
            logger.info(f"Found {len(recent_uids)} emails from last 7 days")
            
            # Search unread emails
            unread_uids = reader.search_emails(unread_only=True)
            logger.info(f"Found {len(unread_uids)} unread emails")
            
            assert len(recent_uids) <= len(all_uids)
            assert len(unread_uids) <= len(all_uids)
        
        logger.info("✅ Email search completed successfully")
    
    def test_fetch_real_emails(self, email_reader):
        """Test fetching and parsing real emails."""
        logger.info("Testing real email fetching...")
        
        with email_reader as reader:
            reader.select_mailbox("INBOX")
            
            # Fetch recent emails (limit to 5 for testing)
            emails = reader.fetch_emails(
                limit=5,
                since_date=datetime.now() - timedelta(days=30)
            )
            
            logger.info(f"Fetched {len(emails)} emails for testing")
            
            if emails:
                # Test first email
                email = emails[0]
                
                # Verify required fields
                assert "uid" in email
                assert "subject" in email
                assert "sender" in email
                assert "date" in email
                assert "body" in email
                assert "is_newsletter" in email
                
                logger.info(f"✅ Sample email: {email['subject'][:50]}...")
                logger.info(f"✅ From: {email['sender']}")
                logger.info(f"✅ Newsletter: {email['is_newsletter']}")
                
                if email["is_newsletter"]:
                    logger.info(f"✅ Newsletter type: {email.get('newsletter_type', 'unknown')}")
            else:
                logger.warning("No emails found in the test account")
        
        logger.info("✅ Email fetching completed successfully")
    
    def test_newsletter_identification(self, email_reader):
        """Test newsletter identification with real emails."""
        logger.info("Testing newsletter identification...")
        
        with email_reader as reader:
            reader.select_mailbox("INBOX")
            
            # Fetch more emails to find newsletters
            emails = reader.fetch_emails(
                limit=20,
                since_date=datetime.now() - timedelta(days=30)
            )
            
            newsletters = reader.filter_newsletters(emails)
            
            logger.info(f"Identified {len(newsletters)} newsletters out of {len(emails)} emails")
            
            # Log details of identified newsletters
            for newsletter in newsletters[:3]:  # Show first 3
                logger.info(
                    f"Newsletter: {newsletter['subject'][:50]} "
                    f"from {newsletter['sender']} "
                    f"(type: {newsletter.get('newsletter_type', 'unknown')})"
                )
            
            # Verify newsletter properties
            for newsletter in newsletters:
                assert newsletter["is_newsletter"] is True
                assert "newsletter_type" in newsletter
        
        logger.info("✅ Newsletter identification completed successfully")
    
    def test_get_recent_newsletters(self, email_reader):
        """Test the high-level newsletter collection method."""
        logger.info("Testing recent newsletter collection...")
        
        with email_reader as reader:
            # Get newsletters from last 7 days
            newsletters = reader.get_recent_newsletters(
                days=7,
                limit=10
            )
            
            logger.info(f"Collected {len(newsletters)} recent newsletters")
            
            # Verify all returned items are newsletters
            for newsletter in newsletters:
                assert newsletter["is_newsletter"] is True
            
            # Log newsletter details
            for i, newsletter in enumerate(newsletters[:3], 1):
                logger.info(
                    f"{i}. {newsletter['subject'][:60]}... "
                    f"({newsletter.get('newsletter_type', 'unknown')})"
                )
        
        logger.info("✅ Recent newsletter collection completed successfully")
    
    @pytest.mark.slow
    def test_large_inbox_handling(self, email_reader):
        """Test handling larger inbox (marked as slow test)."""
        logger.info("Testing large inbox handling...")
        
        with email_reader as reader:
            reader.select_mailbox("INBOX")
            
            # Try to fetch more emails with pagination
            emails = reader.fetch_emails(
                limit=50,
                since_date=datetime.now() - timedelta(days=90)
            )
            
            logger.info(f"Successfully handled {len(emails)} emails from large date range")
            
            if len(emails) > 20:
                # Test processing time for larger batch
                import time
                start_time = time.time()
                
                newsletters = reader.filter_newsletters(emails)
                
                end_time = time.time()
                processing_time = end_time - start_time
                
                logger.info(
                    f"Processed {len(emails)} emails in {processing_time:.2f} seconds "
                    f"({processing_time/len(emails)*1000:.1f}ms per email)"
                )
                
                assert processing_time < 30  # Should process within 30 seconds
        
        logger.info("✅ Large inbox handling completed successfully")


class TestRealEmailConfiguration:
    """Test configuration management for real email testing."""
    
    def test_load_test_configuration(self):
        """Test loading test configuration file."""
        try:
            config = load_config("config/.env.test")
            
            # Basic configuration should be present
            assert config.email.address
            assert config.email.password
            assert config.openai.api_key
            
            logger.info("✅ Test configuration loaded successfully")
            
        except (ConfigurationError, FileNotFoundError):
            pytest.skip("Test configuration file not found or invalid")
    
    def test_configuration_validation(self):
        """Test configuration validation with real values."""
        try:
            config = load_config("config/.env.test")
            validate_config(config)  # Should not raise exception
            
            logger.info("✅ Configuration validation passed")
            
        except (ConfigurationError, FileNotFoundError):
            pytest.skip("Test configuration not available or invalid")
    
    def test_missing_configuration_handling(self):
        """Test handling of missing configuration."""
        # Try loading from non-existent file
        with pytest.raises(ConfigurationError):
            load_config("non_existent_file.env")
        
        logger.info("✅ Correctly handled missing configuration file")


class TestEmailDataPersistence:
    """Test saving email data for debugging and analysis."""
    
    @pytest.fixture
    def config(self):
        """Load test configuration."""
        try:
            return load_config("config/.env.test")
        except (ConfigurationError, FileNotFoundError):
            pytest.skip("Test configuration not available")
    
    def test_save_raw_emails(self, config):
        """Test saving raw email data for debugging."""
        if not config.testing.save_raw_emails:
            pytest.skip("Raw email saving disabled in configuration")
        
        # Ensure raw email directory exists
        raw_dir = Path(config.testing.raw_email_dir)
        raw_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Raw email directory: {raw_dir}")
        assert raw_dir.exists()
        
        logger.info("✅ Raw email directory setup completed")
    
    def test_save_processed_newsletters(self, config):
        """Test saving processed newsletter data."""
        if not config.testing.save_processed_newsletters:
            pytest.skip("Processed newsletter saving disabled in configuration")
        
        # Ensure processed directory exists
        processed_dir = Path(config.testing.processed_dir)
        processed_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Processed newsletter directory: {processed_dir}")
        assert processed_dir.exists()
        
        logger.info("✅ Processed newsletter directory setup completed")


# Utility functions for manual testing and debugging
def manual_test_connection():
    """Manual test function for debugging connection issues."""
    print("🔍 Manual Email Connection Test")
    print("=" * 50)
    
    try:
        config = load_config("config/.env.test")
        print(f"✅ Configuration loaded")
        print(f"   Email: {config.email.address}")
        print(f"   IMAP Server: {config.email.imap_server}:{config.email.imap_port}")
        
        reader = EmailReader(
            imap_server=config.email.imap_server,
            imap_port=config.email.imap_port,
            email_address=config.email.address,
            password=config.email.password,
        )
        
        print(f"🔄 Attempting connection...")
        with reader as r:
            status, count = r.select_mailbox("INBOX")
            print(f"✅ Connected successfully!")
            print(f"   Mailbox: INBOX")
            print(f"   Total emails: {count}")
            
            # Get recent newsletters
            newsletters = r.get_recent_newsletters(days=7, limit=5)
            print(f"   Recent newsletters: {len(newsletters)}")
            
            for i, newsletter in enumerate(newsletters, 1):
                print(f"   {i}. {newsletter['subject'][:60]}...")
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"   Please check your configuration in config/.env.test")


if __name__ == "__main__":
    # Run manual test if executed directly
    manual_test_connection()