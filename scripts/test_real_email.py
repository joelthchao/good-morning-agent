#!/usr/bin/env python3
"""
Real Email Testing Script for Good Morning Agent.

This script helps you test the EmailReader module with real Gmail accounts.
It provides step-by-step guidance for setting up test credentials and running
integration tests.

Usage:
    python scripts/test_real_email.py --setup    # Setup wizard
    python scripts/test_real_email.py --test     # Run tests
    python scripts/test_real_email.py --connect  # Test connection only
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ruff: noqa: E402
from src.utils.config import load_config, validate_config, ConfigurationError
from src.collectors.email_reader import EmailReader


def setup_logging():
    """Setup logging for the test script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


def print_banner():
    """Print welcome banner."""
    print("=" * 60)
    print("🌅 Good Morning Agent - Real Email Testing")
    print("=" * 60)
    print()


def check_prerequisites():
    """Check if prerequisites are met."""
    print("🔍 Checking prerequisites...")

    # Check if config directory exists
    config_dir = Path("config")
    if not config_dir.exists():
        print("❌ Config directory not found. Creating...")
        config_dir.mkdir()

    # Check if .env.test.example exists
    env_example = config_dir / ".env.test.example"
    if not env_example.exists():
        print("❌ .env.test.example not found")
        return False

    # Check if .env.test exists
    env_test = config_dir / ".env.test"
    if not env_test.exists():
        print("⚠️  .env.test not found - you'll need to create it")
        return False

    print("✅ Prerequisites check passed")
    return True


def setup_wizard():
    """Interactive setup wizard for test configuration."""
    print("🧙‍♂️ Setup Wizard")
    print("-" * 20)

    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please:")
        print("1. Ensure config/.env.test.example exists")
        print("2. Copy it to config/.env.test")
        print("3. Fill in your test credentials")
        return False

    print("\n📋 To set up real email testing, follow these steps:")
    print()
    print("1. 📧 Create Test Gmail Account:")
    print("   - Go to https://accounts.google.com/signup")
    print("   - Create account like: test-good-morning-agent@gmail.com")
    print("   - Use a strong password and enable 2FA")
    print()

    print("2. 🔧 Configure Gmail Settings:")
    print("   - Login to your test Gmail account")
    print("   - Go to Settings → 'See all settings' → 'Forwarding and POP/IMAP'")
    print("   - Enable IMAP access")
    print("   - Save changes")
    print()

    print("3. 🔐 Generate App Password:")
    print("   - Go to Google Account settings")
    print("   - Security → App passwords")
    print("   - Generate password for 'Mail' application")
    print("   - Copy the 16-character password")
    print()

    print("4. ⚙️  Configure Environment File:")
    env_test_path = Path("config/.env.test")
    print(f"   - Edit {env_test_path}")
    print("   - Set NEWSLETTER_EMAIL to your test Gmail")
    print("   - Set NEWSLETTER_APP_PASSWORD to your app password")
    print("   - Set OPENAI_API_KEY if you have one")
    print("   - Set RUN_INTEGRATION_TESTS=true")
    print()

    print("5. 📰 Subscribe to Test Newsletters:")
    print("   - Subscribe your test account to a few newsletters:")
    print("     • TLDR Newsletter (tldr.tech)")
    print("     • Pragmatic Engineer (blog.pragmaticengineer.com)")
    print("     • Any Substack newsletter")
    print("   - Wait for a few newsletters to arrive")
    print()

    print("6. 🧪 Run Tests:")
    print("   python scripts/test_real_email.py --test")
    print()

    return True


def test_connection_only() -> bool:
    """Test email connection without running full test suite."""
    print("🔌 Testing Email Connection...")
    print("-" * 30)

    try:
        # Load configuration
        config = load_config("config/.env.test")
        validate_config(config)

        print("✅ Configuration loaded")
        print(f"   📧 Email: {config.email.address}")
        print(f"   🌐 IMAP: {config.email.imap_server}:{config.email.imap_port}")
        print()

        # Test connection
        reader = EmailReader(
            imap_server=config.email.imap_server,
            imap_port=config.email.imap_port,
            email_address=config.email.address,
            password=config.email.password,
            max_retries=2,
        )

        print("🔄 Connecting to IMAP server...")
        with reader as r:
            status, count = r.select_mailbox("INBOX")
            print("✅ Connection successful!")
            print(f"   📨 Inbox messages: {count}")

            # Get recent emails
            print("\n📬 Checking for recent emails...")
            emails = r.fetch_emails(limit=5)
            print(f"   Found {len(emails)} recent emails")

            # Check for newsletters
            newsletters = r.filter_newsletters(emails)
            print(f"   Found {len(newsletters)} newsletters")

            if newsletters:
                print("\n📰 Sample newsletters:")
                for i, newsletter in enumerate(newsletters[:3], 1):
                    print(f"   {i}. {newsletter['subject'][:50]}...")
                    print(f"      From: {newsletter['sender']}")
                    print(f"      Type: {newsletter.get('newsletter_type', 'unknown')}")
                    print()
            else:
                print(
                    "   ⚠️  No newsletters found. Consider subscribing to some for testing."
                )

        print("🎉 Connection test completed successfully!")
        return True

    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        print("\n💡 Suggestions:")
        print("- Check that config/.env.test exists")
        print("- Verify all required fields are filled")
        print("- Run setup wizard: python scripts/test_real_email.py --setup")
        return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n💡 Troubleshooting:")
        print("- Verify Gmail IMAP is enabled")
        print("- Check email address and app password")
        print("- Ensure app password is 16 characters")
        print("- Try generating a new app password")
        return False


def run_integration_tests() -> bool:
    """Run the full integration test suite."""
    print("🧪 Running Integration Tests...")
    print("-" * 35)

    try:
        import subprocess

        # Check if pytest is available
        result = subprocess.run(
            ["uv", "run", "pytest", "--version"], capture_output=True, text=True
        )

        if result.returncode != 0:
            print("❌ pytest not available. Install with: uv sync")
            return False

        # Run integration tests
        print("🔄 Running integration tests...")
        result = subprocess.run(
            [
                "uv",
                "run",
                "pytest",
                "tests/integration/test_real_email_integration.py",
                "-v",
                "--tb=short",
            ]
        )

        success = result.returncode == 0

        if success:
            print("\n🎉 All integration tests passed!")
        else:
            print("\n❌ Some tests failed. Check output above.")

        return success

    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Real Email Testing for Good Morning Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/test_real_email.py --setup     # Run setup wizard
  python scripts/test_real_email.py --connect   # Test connection only
  python scripts/test_real_email.py --test      # Run full test suite
        """,
    )

    parser.add_argument(
        "--setup", action="store_true", help="Run interactive setup wizard"
    )

    parser.add_argument(
        "--connect", action="store_true", help="Test email connection only"
    )

    parser.add_argument(
        "--test", action="store_true", help="Run full integration test suite"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    # Print banner
    print_banner()

    # Default to setup if no arguments
    if not any([args.setup, args.connect, args.test]):
        args.setup = True

    success = True

    if args.setup:
        success = setup_wizard()

    if args.connect:
        success = test_connection_only() and success

    if args.test:
        success = run_integration_tests() and success

    print("\n" + "=" * 60)
    if success:
        print("🎉 All operations completed successfully!")
    else:
        print("❌ Some operations failed. Check output above.")

    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
