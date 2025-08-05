"""
Configuration management for Good Morning Agent.

This module handles loading and validating environment configuration
with proper security practices for sensitive data.
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""

    pass


@dataclass
class EmailConfig:
    """Email configuration settings."""

    imap_server: str
    imap_port: int
    smtp_server: str
    smtp_port: int
    address: str
    password: str
    sender_email: str | None = None
    sender_password: str | None = None
    recipient_email: str | None = None


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""

    api_key: str
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000


@dataclass
class ProcessingConfig:
    """Newsletter processing configuration."""

    max_newsletters_per_run: int = 10
    days_to_look_back: int = 1
    summary_length: int = 200
    newsletter_whitelist: list[str] | None = None
    newsletter_blacklist: list[str] | None = None


@dataclass
class TestingConfig:
    """Testing and development configuration."""

    testing: bool = False
    log_level: str = "INFO"
    run_integration_tests: bool = False
    save_raw_emails: bool = False
    save_processed_newsletters: bool = False
    enable_debug_logging: bool = False
    raw_email_dir: str = "data/raw_emails"
    processed_dir: str = "data/processed"


@dataclass
class Config:
    """Main configuration container."""

    email: EmailConfig
    openai: OpenAIConfig
    processing: ProcessingConfig
    testing: TestingConfig


def load_config(env_file: str | None = None) -> Config:
    """
    Load configuration from environment variables.

    Args:
        env_file: Optional path to .env file. If None, will try to load
                  from .env, .env.test, or environment variables.

    Returns:
        Configured Config object

    Raises:
        ConfigurationError: If required configuration is missing or invalid
    """
    # Try to load from environment file
    if env_file:
        env_path = Path(env_file)
        if not env_path.exists():
            raise ConfigurationError(f"Environment file not found: {env_file}")
        load_dotenv(env_path)
    else:
        # Try common environment file locations
        project_root = Path(__file__).parent.parent.parent
        env_files = [
            project_root / "config" / ".env.test",
            project_root / "config" / ".env",
            project_root / ".env.test",
            project_root / ".env",
        ]

        for env_path in env_files:
            if env_path.exists():
                logger.info(f"Loading configuration from {env_path}")
                load_dotenv(env_path)
                break
        else:
            logger.info("No environment file found, using system environment variables")

    try:
        # Load email configuration
        email_config = EmailConfig(
            imap_server=_get_required_env("EMAIL_IMAP_SERVER", "imap.gmail.com"),
            imap_port=int(_get_required_env("EMAIL_IMAP_PORT", "993")),
            smtp_server=_get_required_env("EMAIL_SMTP_SERVER", "smtp.gmail.com"),
            smtp_port=int(_get_required_env("EMAIL_SMTP_PORT", "587")),
            address=_get_required_env("NEWSLETTER_EMAIL"),
            password=_get_required_env("NEWSLETTER_APP_PASSWORD"),
            sender_email=os.getenv("SENDER_EMAIL"),
            sender_password=os.getenv("SENDER_APP_PASSWORD"),
            recipient_email=os.getenv("RECIPIENT_EMAIL"),
        )

        # Load OpenAI configuration
        openai_config = OpenAIConfig(
            api_key=_get_required_env("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
        )

        # Load processing configuration
        whitelist_str = os.getenv("NEWSLETTER_WHITELIST")
        blacklist_str = os.getenv("NEWSLETTER_BLACKLIST")

        processing_config = ProcessingConfig(
            max_newsletters_per_run=int(os.getenv("MAX_NEWSLETTERS_PER_RUN", "10")),
            days_to_look_back=int(os.getenv("DAYS_TO_LOOK_BACK", "1")),
            summary_length=int(os.getenv("SUMMARY_LENGTH", "200")),
            newsletter_whitelist=whitelist_str.split(",") if whitelist_str else None,
            newsletter_blacklist=blacklist_str.split(",") if blacklist_str else None,
        )

        # Load testing configuration
        testing_config = TestingConfig(
            testing=_get_bool_env("TESTING", False),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            run_integration_tests=_get_bool_env("RUN_INTEGRATION_TESTS", False),
            save_raw_emails=_get_bool_env("SAVE_RAW_EMAILS", False),
            save_processed_newsletters=_get_bool_env(
                "SAVE_PROCESSED_NEWSLETTERS", False
            ),
            enable_debug_logging=_get_bool_env("ENABLE_DEBUG_LOGGING", False),
            raw_email_dir=os.getenv("RAW_EMAIL_DIR", "data/raw_emails"),
            processed_dir=os.getenv("PROCESSED_DIR", "data/processed"),
        )

        return Config(
            email=email_config,
            openai=openai_config,
            processing=processing_config,
            testing=testing_config,
        )

    except (ValueError, TypeError) as e:
        raise ConfigurationError(f"Invalid configuration value: {e}") from e


def validate_config(config: Config) -> None:
    """
    Validate configuration for completeness and correctness.

    Args:
        config: Configuration to validate

    Raises:
        ConfigurationError: If configuration is invalid
    """
    # Validate email configuration
    if not config.email.address:
        raise ConfigurationError("NEWSLETTER_EMAIL is required")

    if not config.email.password:
        raise ConfigurationError("NEWSLETTER_APP_PASSWORD is required")

    if "@" not in config.email.address:
        raise ConfigurationError("Email address must be valid")

    # Validate OpenAI configuration
    if not config.openai.api_key:
        raise ConfigurationError("OPENAI_API_KEY is required")

    if not config.openai.api_key.startswith("sk-"):
        raise ConfigurationError("OPENAI_API_KEY must start with 'sk-'")

    # Validate port numbers
    if not (1 <= config.email.imap_port <= 65535):
        raise ConfigurationError("EMAIL_IMAP_PORT must be between 1 and 65535")

    if not (1 <= config.email.smtp_port <= 65535):
        raise ConfigurationError("EMAIL_SMTP_PORT must be between 1 and 65535")

    # Validate processing limits
    if config.processing.max_newsletters_per_run <= 0:
        raise ConfigurationError("MAX_NEWSLETTERS_PER_RUN must be positive")

    if config.processing.days_to_look_back <= 0:
        raise ConfigurationError("DAYS_TO_LOOK_BACK must be positive")

    logger.info("Configuration validation passed")


def _get_required_env(key: str, default: str | None = None) -> str:
    """Get required environment variable with optional default."""
    value = os.getenv(key, default)
    if not value:
        raise ConfigurationError(f"Required environment variable {key} is not set")
    return value


def _get_bool_env(key: str, default: bool = False) -> bool:
    """Get boolean environment variable."""
    value = os.getenv(key, "").lower()
    if value in ("true", "1", "yes", "on"):
        return True
    elif value in ("false", "0", "no", "off"):
        return False
    else:
        return default


def setup_logging(config: Config) -> None:
    """Setup logging based on configuration."""
    level = getattr(logging, config.testing.log_level.upper(), logging.INFO)

    # Configure basic logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Enable debug logging if requested
    if config.testing.enable_debug_logging:
        logging.getLogger("src").setLevel(logging.DEBUG)
        logging.getLogger("imaplib").setLevel(logging.DEBUG)

    logger.info(f"Logging configured at {config.testing.log_level} level")


# Convenience function for quick loading
def get_config() -> Config:
    """Get validated configuration."""
    config = load_config()
    validate_config(config)
    setup_logging(config)
    return config
