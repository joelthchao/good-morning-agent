#!/usr/bin/env python3
"""
Interactive environment configuration script.
Helps users safely configure their .env.test file.
"""

import getpass
import re
from pathlib import Path


def configure_environment():
    """Interactive configuration of .env.test file."""
    print("🔧 Good Morning Agent - Environment Configuration")
    print("=" * 55)
    print()

    env_file = Path("config/.env.test")

    if not env_file.exists():
        print("❌ config/.env.test not found!")
        print("Please run: cp config/.env.test.example config/.env.test")
        return False

    print("📝 Please provide your Gmail test account information:")
    print("(Press Enter to skip optional fields)")
    print()

    # Get email address
    while True:
        email = input("📧 Gmail address (e.g., test-agent@gmail.com): ").strip()
        if not email:
            print("❌ Email address is required!")
            continue
        if "@gmail.com" not in email:
            print("❌ Please use a Gmail address (@gmail.com)")
            continue
        break

    # Get app password
    while True:
        print("\n🔐 Gmail App Password:")
        print("(Should be 16 characters, may include spaces)")
        password = getpass.getpass("App Password: ").strip()

        if not password:
            print("❌ App password is required!")
            continue

        # Remove spaces and check length
        clean_password = password.replace(" ", "")
        if len(clean_password) != 16:
            print(
                f"❌ App password should be 16 characters (got {len(clean_password)})"
            )
            retry = input("Try again? (y/n): ").lower()
            if retry != "y":
                break
            continue
        break

    # Get OpenAI API key (optional)
    print("\n🤖 OpenAI API Key (optional, for AI testing):")
    openai_key = getpass.getpass("OpenAI API Key (or press Enter to skip): ").strip()

    # Read current .env.test content
    content = env_file.read_text()

    # Update configuration
    content = re.sub(r"EMAIL_ADDRESS=.*", f"EMAIL_ADDRESS={email}", content)

    content = re.sub(r"EMAIL_PASSWORD=.*", f"EMAIL_PASSWORD={clean_password}", content)

    if openai_key and openai_key.startswith("sk-"):
        content = re.sub(r"OPENAI_API_KEY=.*", f"OPENAI_API_KEY={openai_key}", content)

    # Enable integration tests
    content = re.sub(
        r"RUN_INTEGRATION_TESTS=false", "RUN_INTEGRATION_TESTS=true", content
    )

    # Write updated configuration
    env_file.write_text(content)

    print("\n✅ Configuration saved to config/.env.test")
    print()
    print("🔒 Security reminders:")
    print("• Never commit .env.test to version control")
    print("• Keep your app password secure")
    print("• Use only test accounts, never production accounts")
    print()

    return True


def test_configuration():
    """Test the configuration by attempting to load it."""
    print("🧪 Testing configuration...")

    try:
        import sys
        from pathlib import Path

        # Add project root to path
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))

        from src.utils.config import load_config, validate_config

        config = load_config("config/.env.test")
        validate_config(config)

        print("✅ Configuration validation passed!")
        print(f"   Email: {config.email.address}")
        print(f"   IMAP: {config.email.imap_server}:{config.email.imap_port}")
        print(f"   Integration tests: {config.testing.run_integration_tests}")

        return True

    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


def main():
    """Main configuration flow."""
    print()

    # Configure environment
    if not configure_environment():
        return 1

    # Test configuration
    if not test_configuration():
        print("\n💡 Please check your configuration and try again.")
        return 1

    print("\n🎉 Configuration completed successfully!")
    print("\n🚀 Next steps:")
    print("1. Test connection: uv run python scripts/test_real_email.py --connect")
    print("2. Subscribe to newsletters in your test Gmail account")
    print("3. Run full tests: uv run python scripts/test_real_email.py --test")
    print()

    return 0


if __name__ == "__main__":
    exit(main())
