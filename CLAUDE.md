# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Good Morning Agent is a privacy-first personal information aggregation tool that generates AI-powered daily summaries from newsletters, weather, and news. The system processes content locally and delivers 10-minute reading digests via email.

## Core Architecture

The system is built around 4 key components:

1. **Email Collection** (`src/collectors/`) - IMAP-based newsletter collection from dedicated mailboxes
2. **Content Processing** (`src/processors/`) - HTML parsing, content extraction, and data cleaning
3. **AI Summarization** (`src/processors/`) - OpenAI API integration for deep content analysis
4. **Email Delivery** (`src/senders/`) - SMTP-based HTML email generation and sending

### Data Flow
```
Scheduled Trigger → Newsletter Collection (IMAP) → Content Parsing → AI Summarization → Email Delivery (SMTP)
```

## Privacy-First Design

**Critical Design Decision**: The system uses dedicated collection mailboxes rather than accessing personal inboxes. Users re-subscribe to newsletters using a dedicated Gmail account (e.g., `good-morning-newsletters@gmail.com`), ensuring complete privacy isolation.

## Development Commands

### Environment Setup with UV
```bash
# Initial setup (installs Python 3.12 and dependencies)
make setup

# Or manually:
uv python install 3.12
uv sync

# Setup environment variables
cp config/.env.example config/.env
# Edit .env with actual API keys and credentials
```

### Development Workflow
```bash
# All-in-one development setup
make dev

# Code formatting
make format
# or: uv run black src/ tests/ && uv run isort src/ tests/

# Code quality checks
make check
# or: uv run flake8 src/ tests/ && uv run mypy src/

# Run tests
make test
# or: uv run pytest

# Run specific test types
make test-unit          # Unit tests only
make test-integration   # Integration tests only
make test-coverage      # With coverage report

# Run application
make run
# or: uv run python -m src.main
```

### Database Operations
```bash
# Initialize local database
make db-init

# Local SQLite database is created automatically at data/good_morning.db
# No manual setup required for MVP
```

### Docker Operations
```bash
# Build Docker image
make docker-build

# Run in Docker
make docker-run

# Development with Docker
make docker-dev
```

## Key Configuration

### Required Environment Variables (.env)
- `NEWSLETTER_EMAIL` - Dedicated collection mailbox
- `NEWSLETTER_APP_PASSWORD` - Gmail app-specific password
- `SENDER_EMAIL` - Email address for sending summaries
- `SENDER_APP_PASSWORD` - Gmail app password for sender
- `RECIPIENT_EMAIL` - Target email for daily summaries
- `OPENAI_API_KEY` - OpenAI API key for summarization
- `WEATHER_API_KEY` - Weather service API key
- `DAILY_RUN_TIME` - Execution time (default: 07:00)

### Newsletter Sources (Initial Support)
- **tl;dr** (`newsletter@tldr.tech`) - Tech news summaries
- **Deep Learning Weekly** (`noreply@deeplearningweekly.com`) - AI/ML content
- **Pragmatic Engineer** (`newsletter@pragmatic-engineer.com`) - Software engineering

## Implementation Priority

Based on technical implementation guide, development should follow this sequence:
1. IMAP email collection module (foundation)
2. AI summarization with OpenAI integration
3. SMTP email delivery system
4. Scheduling and error handling

## Cost Management

The system includes built-in cost controls:
- `DAILY_TOKEN_LIMIT` - OpenAI API usage limits
- `SUMMARY_MAX_LENGTH` - Content length restrictions
- Model selection via `OPENAI_MODEL` (gpt-3.5-turbo vs gpt-4)

## Architecture Decisions

**MVP Strategy**: Local Python script deployment before cloud migration
**Database**: SQLite for local development, PostgreSQL for production
**Scheduling**: Cron jobs for local, Cloud Scheduler for GCP deployment
**Error Handling**: Exponential backoff for IMAP/SMTP operations, fallback summaries for AI failures

## Testing Strategy

Focus on integration testing for email operations and API interactions:
- Mock IMAP servers for newsletter collection tests
- Mock OpenAI API responses for summarization tests
- Test email template rendering and SMTP delivery
- Environment variable validation and error handling

## Package Management with UV

This project uses **uv** as the primary Python package manager and version manager:

- **Python Version**: Locked to 3.12 (see `.python-version`)
- **Dependencies**: Managed via `pyproject.toml` (modern Python standard)
- **Virtual Environment**: Automatically managed by uv
- **Lock File**: `uv.lock` ensures reproducible builds

### Legacy Compatibility
- `requirements.txt` can be generated via `make requirements` for compatibility
- Original `requirements.txt` is deprecated in favor of `pyproject.toml`

## Security Considerations

- All API keys stored in environment variables
- Gmail app passwords (not primary account passwords)
- No personal email access - dedicated collection accounts only
- Local data processing (no third-party data uploads)