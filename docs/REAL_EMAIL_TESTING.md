# 🌅 Real Email Testing Guide

This guide will help you test the EmailReader module with real Gmail accounts to validate newsletter collection functionality.

## 📋 Overview

Real email testing allows you to:
- Verify IMAP connection with actual Gmail servers
- Test newsletter identification with real newsletter content
- Validate email parsing with various email formats
- Ensure the system works with your actual newsletter subscriptions

## 🔧 Prerequisites

### 1. System Requirements
- Python 3.12+ with uv package manager
- Access to create Gmail accounts
- OpenAI API key (optional, for AI summarization testing)

### 2. Dependencies
All dependencies should already be installed if you've set up the development environment:
```bash
uv sync  # Install all dependencies including test dependencies
```

## 🚀 Quick Start

### Option 1: Interactive Setup (Recommended)
```bash
python scripts/test_real_email.py --setup
```

### Option 2: Manual Setup
Follow the detailed steps below.

## 📧 Gmail Account Setup

### Step 1: Create Test Gmail Account
1. Go to [Google Account Creation](https://accounts.google.com/signup)
2. Create a dedicated test account (e.g., `test-good-morning-agent@gmail.com`)
3. Use a strong password and enable 2-Factor Authentication
4. **Important**: Use a separate account, not your main Gmail

### Step 2: Enable IMAP Access
1. Login to your test Gmail account
2. Go to **Settings** → **See all settings**
3. Click **Forwarding and POP/IMAP** tab
4. Select **Enable IMAP**
5. Click **Save Changes**

### Step 3: Generate App Password
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "2-Step Verification" → **App passwords**
3. Select app: **Mail**
4. Select device: **Other** (enter "Good Morning Agent")
5. **Copy the 16-character password** (you'll need this)

## ⚙️ Configuration Setup

### Step 1: Create Test Configuration
```bash
# Copy the example configuration
cp config/.env.test.example config/.env.test
```

### Step 2: Edit Configuration
Edit `config/.env.test` with your real test values:

```bash
# Essential settings for testing
NEWSLETTER_EMAIL=your-test-account@gmail.com
NEWSLETTER_APP_PASSWORD=your-16-character-app-password
OPENAI_API_KEY=sk-your-openai-key-here  # Optional

# Enable integration tests
RUN_INTEGRATION_TESTS=true
TESTING=true
LOG_LEVEL=DEBUG

# Test limits (to avoid costs/rate limits)
MAX_NEWSLETTERS_PER_RUN=5
DAYS_TO_LOOK_BACK=7
```

### Step 3: Secure Your Configuration
```bash
# Ensure .env.test is in .gitignore (it should be already)
echo "config/.env.test" >> .gitignore
```

## 📰 Newsletter Setup

To test newsletter identification, subscribe your test account to a few newsletters:

### Recommended Test Newsletters
- **TLDR Newsletter**: Quick tech news (https://tldr.tech)
- **Pragmatic Engineer**: Software engineering insights
- **Morning Brew**: Business news (optional)
- **Any Substack newsletter**: For testing Substack integration

### Subscribe Process
1. Use your **test Gmail account** to subscribe
2. Confirm subscriptions via email
3. Wait for 2-3 newsletters to arrive (may take 1-2 days)
4. Verify newsletters appear in your test inbox

## 🧪 Running Tests

### Quick Connection Test
Test your configuration without running full tests:
```bash
python scripts/test_real_email.py --connect
```

Expected output:
```
🔌 Testing Email Connection...
✅ Configuration loaded
   📧 Email: test-account@gmail.com
   🌐 IMAP: imap.gmail.com:993

🔄 Connecting to IMAP server...
✅ Connection successful!
   📨 Inbox messages: 42
   
📬 Checking for recent emails...
   Found 5 recent emails
   Found 2 newsletters

📰 Sample newsletters:
   1. TLDR Newsletter - Daily Tech Update...
      From: dan@tldrnewsletter.com
      Type: technology
```

### Full Integration Tests
Run comprehensive integration tests:
```bash
python scripts/test_real_email.py --test
```

Or run directly with pytest:
```bash
uv run pytest tests/integration/test_real_email_integration.py -v
```

### Manual Testing
For debugging, you can run individual components:
```python
# In Python shell
from src.utils.config import load_config
from src.collectors.email_reader import EmailReader

config = load_config("config/.env.test")
reader = EmailReader(
    imap_server=config.email.imap_server,
    imap_port=config.email.imap_port,
    email_address=config.email.address,
    password=config.email.password,
)

# Test connection
with reader as r:
    newsletters = r.get_recent_newsletters(days=7, limit=5)
    for newsletter in newsletters:
        print(f"📰 {newsletter['subject']}")
```

## 🔍 Test Coverage

The integration tests cover:

### Connection Management
- ✅ IMAP connection with real credentials
- ✅ Authentication failure handling
- ✅ Connection retry logic
- ✅ Proper cleanup and disconnection

### Email Operations
- ✅ Email searching with various criteria
- ✅ Email fetching and parsing
- ✅ Handling different email formats (HTML/text)
- ✅ Large inbox handling with pagination

### Newsletter Processing
- ✅ Newsletter identification from real emails
- ✅ Content classification (tech, business, news)
- ✅ Priority-based filtering
- ✅ Content extraction and cleaning

### Performance & Reliability
- ✅ Timeout handling
- ✅ Error recovery
- ✅ Rate limit compliance
- ✅ Memory efficiency with large inboxes

## 🐛 Troubleshooting

### Common Issues

#### 1. Authentication Failures
```
❌ Connection failed: Authentication failed
```
**Solutions:**
- Verify IMAP is enabled in Gmail settings
- Check that you're using the 16-character app password, not your regular password
- Ensure 2FA is enabled on your Google account
- Try generating a new app password

#### 2. No Newsletters Found
```
⚠️ No newsletters found. Consider subscribing to some for testing.
```
**Solutions:**
- Subscribe to newsletters and wait for them to arrive
- Check that newsletters are in INBOX (not promotions folder)
- Try increasing `DAYS_TO_LOOK_BACK` in configuration

#### 3. IMAP Connection Timeouts
```
❌ Connection failed: timeout
```
**Solutions:**
- Check your internet connection
- Verify Gmail IMAP server settings
- Try increasing timeout values in configuration

#### 4. Configuration Errors
```
❌ Configuration error: NEWSLETTER_EMAIL is required
```
**Solutions:**
- Ensure `config/.env.test` exists and is properly formatted
- Check that all required fields are filled
- Run setup wizard: `python scripts/test_real_email.py --setup`

### Debug Mode
Enable detailed logging for debugging:
```bash
# In config/.env.test
LOG_LEVEL=DEBUG
ENABLE_DEBUG_LOGGING=true
```

### Email Data Inspection
Save raw emails for debugging:
```bash
# In config/.env.test
SAVE_RAW_EMAILS=true
SAVE_PROCESSED_NEWSLETTERS=true
```

## 🔒 Security Best Practices

### 1. Use Dedicated Test Accounts
- Never use your primary Gmail account for testing
- Create dedicated test accounts for this purpose
- Use strong, unique passwords

### 2. Protect Credentials
- Never commit `.env.test` to version control
- Use app passwords, not regular passwords
- Regularly rotate app passwords

### 3. Limit Access
- Only enable necessary Gmail features (IMAP)
- Use minimal required permissions
- Monitor account activity regularly

### 4. Environment Isolation
- Keep test credentials separate from production
- Use different API keys for testing
- Limit test account newsletter subscriptions

## 📊 Expected Results

After successful setup, you should see:

### Connection Test Output
```
✅ Configuration loaded
✅ Connection successful!
📨 Inbox messages: 15+
📰 Found 3+ newsletters
```

### Integration Test Results
```
test_real_imap_connection PASSED
test_search_real_emails PASSED  
test_fetch_real_emails PASSED
test_newsletter_identification PASSED
test_get_recent_newsletters PASSED
```

### Newsletter Identification
The system should correctly identify:
- Newsletter vs regular emails
- Newsletter types (technology, business, news)
- Content extraction from HTML emails
- Sender domain patterns

## 🎯 Next Steps

Once real email testing is successful:

1. **Expand Newsletter Sources**: Subscribe to more newsletters for testing
2. **Test AI Summarization**: Add OpenAI API key and test content summarization
3. **Performance Testing**: Test with larger inboxes and more newsletters  
4. **Email Automation**: Set up automatic daily collection
5. **Integration with Other Modules**: Connect to processors and senders

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review logs with `LOG_LEVEL=DEBUG`
3. Verify Gmail account settings
4. Test with the connection-only mode first
5. Create a GitHub issue with detailed error logs

Remember: Real email testing validates that your implementation works with actual email providers and real newsletter content, giving you confidence in the system's reliability.