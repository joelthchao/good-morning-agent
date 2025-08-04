.PHONY: help install dev clean test lint format type-check run docker-build docker-run setup

# Default target
help: ## Show this help message
	@echo "Good Morning Agent - Development Commands"
	@echo "========================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Environment setup
setup: ## Initial project setup with uv
	@echo "🚀 Setting up Good Morning Agent development environment..."
	@command -v uv >/dev/null 2>&1 || { echo "❌ uv not found. Please install: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
	uv python install 3.12
	uv sync
	@python scripts/install_hooks.py
	@echo "✅ Setup complete! Virtual environment and Git hooks ready."

install: ## Install production dependencies
	uv sync --no-dev

dev: ## Install development dependencies
	uv sync

# Development commands
run: ## Run the application
	uv run python -m src.main

test: ## Run tests
	uv run pytest

test-unit: ## Run unit tests only
	uv run pytest -m "not integration"

test-integration: ## Run integration tests only
	uv run pytest -m integration

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=src --cov-report=html --cov-report=term

# Code quality
format: ## Format code with black and isort
	uv run black src/ tests/
	uv run isort src/ tests/

lint: ## Run linting checks
	uv run flake8 src/ tests/
	uv run black --check src/ tests/
	uv run isort --check-only src/ tests/

type-check: ## Run type checking with mypy
	uv run mypy src/

check: lint type-check ## Run all code quality checks

# Development utilities
clean: ## Clean up cache and temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/ .mypy_cache/

shell: ## Start interactive shell with project environment
	uv run python

# Environment management
env-info: ## Show environment information
	@echo "Python version:"
	@uv run python --version
	@echo "\nInstalled packages:"
	@uv pip list

requirements: ## Generate requirements.txt for compatibility
	uv pip compile pyproject.toml -o requirements.txt

# Docker commands
docker-build: ## Build Docker image
	docker build -t good-morning-agent:latest .

docker-run: ## Run Docker container
	docker run --rm -it --env-file config/.env good-morning-agent:latest

docker-dev: ## Run Docker container in development mode
	docker run --rm -it -v $(PWD):/app --env-file config/.env good-morning-agent:latest

# Git hooks
install-hooks: ## Install Git hooks for code quality
	@echo "🪝 Installing Git hooks..."
	@python scripts/install_hooks.py

# Configuration
config-check: ## Validate configuration
	@echo "🔍 Checking configuration..."
	@test -f config/.env || { echo "❌ config/.env not found. Copy from config/.env.example"; exit 1; }
	@uv run python -c "from src.utils.config import validate_config; validate_config()" 2>/dev/null || echo "⚠️  Configuration validation script not yet implemented"
	@echo "✅ Configuration check complete"

# Data management
db-init: ## Initialize local database
	@echo "🗄️ Initializing local database..."
	@mkdir -p data
	@uv run python -c "from src.utils.database import init_db; init_db()" 2>/dev/null || echo "⚠️  Database initialization script not yet implemented"

# Scheduling
cron-setup: ## Setup cron job for daily execution
	@echo "⏰ Setting up cron job..."
	@uv run python scripts/setup_cron.py 2>/dev/null || echo "⚠️  Cron setup script not yet implemented"

# Deployment helpers
deploy-local: install config-check db-init ## Prepare for local deployment
	@echo "✅ Local deployment ready"

deploy-check: check test ## Run all checks before deployment
	@echo "✅ Deployment checks passed"