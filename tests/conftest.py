"""
Pytest configuration and shared fixtures for Good Morning Agent tests.

This file contains:
- Common test fixtures
- Mock configurations
- Test data setup
- Environment setup for testing
"""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
from dotenv import load_dotenv


# Test Environment Setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables and configurations."""
    # Load test environment variables
    test_env_path = Path(__file__).parent / ".env.test"
    if test_env_path.exists():
        load_dotenv(test_env_path)

    # Set test-specific environment variables
    os.environ["TESTING"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"

    yield

    # Cleanup after all tests


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_data_dir() -> Path:
    """Path to test data directory."""
    return Path(__file__).parent / "data"


# Email Testing Fixtures
@pytest.fixture
def mock_email_credentials() -> dict[str, str]:
    """Mock email credentials for testing."""
    return {
        "imap_server": "imap.gmail.com",
        "imap_port": "993",
        "email": "test.collector@gmail.com",
        "password": "test_app_password",
    }


@pytest.fixture
def mock_imap_connection():
    """Mock IMAP connection for email testing."""
    with patch("imaplib.IMAP4_SSL") as mock_imap:
        mock_connection = Mock()
        mock_imap.return_value = mock_connection

        # Configure mock behaviors
        mock_connection.login.return_value = ("OK", [b"LOGIN completed"])
        mock_connection.select.return_value = ("OK", [b"10"])  # 10 emails
        mock_connection.search.return_value = ("OK", [b"1 2 3 4 5"])
        mock_connection.logout.return_value = ("BYE", [b"Logging out"])

        yield mock_connection


@pytest.fixture
def sample_email_data() -> dict[str, Any]:
    """Sample email data for testing."""
    return {
        "uid": "123",
        "subject": "Test Newsletter - AI Weekly #42",
        "sender": "newsletter@example.com",
        "date": "Mon, 01 Jan 2024 10:00:00 +0000",
        "content_type": "text/html",
        "body": """
        <html>
        <body>
        <h1>AI Weekly #42</h1>
        <p>This week in AI: GPT-4 improvements, new research papers, and more.</p>
        <div class="article">
            <h2>GPT-4 Gets Better</h2>
            <p>OpenAI announced improvements to GPT-4 with better reasoning capabilities.</p>
        </div>
        <div class="article">
            <h2>New Research: Transformer Architectures</h2>
            <p>Researchers at Stanford published a paper on efficient transformer designs.</p>
        </div>
        </body>
        </html>
        """,
    }


@pytest.fixture
def sample_newsletter_emails() -> list[dict[str, Any]]:
    """Multiple sample newsletter emails for testing."""
    return [
        {
            "uid": "001",
            "subject": "tl;dr - Tech News Summary",
            "sender": "tldr@tldrnewsletter.com",
            "date": "Mon, 01 Jan 2024 06:00:00 +0000",
            "body": "<h1>TLDR</h1><p>Latest in tech: AI breakthroughs, startup funding, and more.</p>",
        },
        {
            "uid": "002",
            "subject": "Deep Learning Weekly #156",
            "sender": "deeplearningweekly@gmail.com",
            "date": "Sun, 31 Dec 2023 20:00:00 +0000",
            "body": "<h1>Deep Learning Weekly</h1><p>New papers in computer vision and NLP.</p>",
        },
        {
            "uid": "003",
            "subject": "The Pragmatic Engineer Newsletter",
            "sender": "gergely@pragmaticengineer.com",
            "date": "Thu, 28 Dec 2023 15:00:00 +0000",
            "body": "<h1>Engineering Insights</h1><p>Software architecture patterns and team management.</p>",
        },
    ]


# AI/OpenAI Testing Fixtures
@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing AI summarization."""
    with patch("openai.OpenAI") as mock_client:
        mock_instance = Mock()
        mock_client.return_value = mock_instance

        # Mock chat completion response
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="Test AI summary of the newsletter content."))
        ]
        mock_instance.chat.completions.create.return_value = mock_response

        yield mock_instance


@pytest.fixture
def sample_ai_summary() -> str:
    """Sample AI-generated summary for testing."""
    return """
    **AI Weekly #42 Summary**

    This week's highlights include:

    1. **GPT-4 Improvements**: OpenAI announced enhanced reasoning capabilities for GPT-4
    2. **Research Breakthrough**: Stanford researchers published efficient transformer architectures

    Key takeaway: The AI field continues rapid advancement with both commercial and academic progress.

    Estimated reading time: 3 minutes
    """


# Email Sending Testing Fixtures
@pytest.fixture
def mock_smtp_connection():
    """Mock SMTP connection for email sending tests."""
    with patch("smtplib.SMTP_SSL") as mock_smtp:
        mock_connection = Mock()
        mock_smtp.return_value = mock_connection

        mock_connection.login.return_value = None
        mock_connection.send_message.return_value = {}
        mock_connection.quit.return_value = None

        yield mock_connection


# Configuration Testing Fixtures
@pytest.fixture
def test_config() -> dict[str, Any]:
    """Test configuration dictionary."""
    return {
        "email": {
            "imap_server": "imap.gmail.com",
            "imap_port": 993,
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "collection_email": "test.collector@gmail.com",
            "sender_email": "test.sender@gmail.com",
        },
        "openai": {
            "api_key": "test_api_key",
            "model": "gpt-4",
            "max_tokens": 1000,
        },
        "processing": {
            "summary_length": 200,
            "max_articles": 10,
        },
    }


# Database/Storage Testing Fixtures
@pytest.fixture
def temp_data_dir(temp_dir) -> Path:
    """Create temporary directories for data storage during tests."""
    data_dir = temp_dir / "data"
    (data_dir / "emails").mkdir(parents=True)
    (data_dir / "summaries").mkdir(parents=True)
    (data_dir / "logs").mkdir(parents=True)
    return data_dir


# Pytest Markers and Custom Fixtures
@pytest.fixture
def skip_integration():
    """Fixture to conditionally skip integration tests."""
    if os.getenv("SKIP_INTEGRATION_TESTS"):
        pytest.skip("Integration tests skipped")


@pytest.fixture
def require_api_keys():
    """Fixture that requires real API keys for testing."""
    required_keys = ["OPENAI_API_KEY", "NEWSLETTER_APP_PASSWORD"]
    missing_keys = [key for key in required_keys if not os.getenv(key)]

    if missing_keys:
        pytest.skip(f"Missing required API keys: {', '.join(missing_keys)}")
