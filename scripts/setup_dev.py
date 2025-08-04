#!/usr/bin/env python3
"""
Development environment setup script for Good Morning Agent.
This script helps set up the development environment using uv.
"""

import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, description: str = "", check: bool = True) -> bool:
    """Run a shell command and handle errors."""
    print(f"🔄 {description or cmd}")
    try:
        result = subprocess.run(
            cmd, shell=True, check=check, capture_output=True, text=True
        )
        if result.stdout:
            print(f"✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr.strip()}")
        return False


def check_prerequisites():
    """Check if required tools are installed."""
    print("🔍 Checking prerequisites...")

    # Check Python version
    if sys.version_info < (3, 12):
        print(f"❌ Python 3.12+ required, found {sys.version}")
        return False

    print(f"✅ Python {sys.version.split()[0]}")

    # Check if uv is installed
    if not run_command("uv --version", "Checking uv installation", check=False):
        print("❌ uv not found. Installing uv...")
        install_cmd = "curl -LsSf https://astral.sh/uv/install.sh | sh"
        if not run_command(install_cmd, "Installing uv"):
            print("❌ Failed to install uv. Please install manually.")
            return False

    return True


def setup_environment():
    """Set up the development environment."""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print(f"📁 Working in: {project_root}")

    # Ensure Python 3.12 is available
    if not run_command("uv python install 3.12", "Installing Python 3.12"):
        return False

    # Create virtual environment and install dependencies
    if not run_command("uv sync", "Installing dependencies"):
        return False

    return True


def setup_config():
    """Set up configuration files."""
    config_example = Path("config/.env.example")
    config_file = Path("config/.env")

    if config_example.exists() and not config_file.exists():
        print("📝 Creating .env file from example...")
        import shutil

        shutil.copy(config_example, config_file)
        print("⚠️  Please edit config/.env with your actual API keys and settings")
    elif config_file.exists():
        print("✅ Configuration file already exists")
    else:
        print("⚠️  No configuration example found")


def create_directories():
    """Create necessary directories."""
    directories = [
        "data/emails",
        "data/summaries",
        "data/logs",
        "tests/unit",
        "tests/integration",
    ]

    print("📁 Creating project directories...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

        # Create .gitkeep files for empty directories
        gitkeep = Path(directory) / ".gitkeep"
        if not gitkeep.exists() and not any(Path(directory).iterdir()):
            gitkeep.touch()

    print("✅ Project directories created")


def setup_git_hooks():
    """Set up git hooks for code quality."""
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        print("⚠️  Not a git repository, skipping git hooks setup")
        return

    pre_commit_hook = hooks_dir / "pre-commit"
    hook_content = """#!/bin/sh
# Good Morning Agent pre-commit hook
echo "🔍 Running pre-commit checks..."

# Run code formatting
uv run black --check src/ tests/ || {
    echo "❌ Code formatting check failed. Run 'make format' to fix."
    exit 1
}

# Run linting
uv run flake8 src/ tests/ || {
    echo "❌ Linting failed. Fix the issues above."
    exit 1
}

# Run type checking
uv run mypy src/ || {
    echo "❌ Type checking failed. Fix the issues above."
    exit 1
}

echo "✅ Pre-commit checks passed!"
"""

    pre_commit_hook.write_text(hook_content)
    pre_commit_hook.chmod(0o755)
    print("✅ Git pre-commit hook installed")


def main():
    """Main setup function."""
    print("🚀 Good Morning Agent - Development Setup")
    print("=" * 50)

    if not check_prerequisites():
        sys.exit(1)

    if not setup_environment():
        sys.exit(1)

    setup_config()
    create_directories()
    setup_git_hooks()

    print("\n🎉 Development environment setup complete!")
    print("\nNext steps:")
    print("1. Edit config/.env with your API keys")
    print("2. Run 'make test' to verify everything works")
    print("3. Run 'make run' to start development")
    print("\nUse 'make help' to see all available commands.")


if __name__ == "__main__":
    main()
