#!/usr/bin/env python3
"""
Install Git hooks for Good Morning Agent.
This script installs pre-commit hooks to ensure code quality.
"""

import shutil
import stat
from pathlib import Path


def install_pre_commit_hook():
    """Install the pre-commit hook."""
    hook_content = """#!/bin/sh
# Good Morning Agent pre-commit hook
# This script runs code quality checks before allowing commits

echo "🔍 Running pre-commit code quality checks..."

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "${RED}❌ uv not found. Please install uv first.${NC}"
    exit 1
fi

# Function to run a check and handle the result
run_check() {
    local check_name="$1"
    local command="$2"
    local fix_command="$3"
    
    echo "${YELLOW}Running $check_name...${NC}"
    
    if eval "$command"; then
        echo "${GREEN}✅ $check_name passed${NC}"
        return 0
    else
        echo "${RED}❌ $check_name failed${NC}"
        if [ -n "$fix_command" ]; then
            echo "${YELLOW}💡 To fix, run: $fix_command${NC}"
        fi
        return 1
    fi
}

# Track if any checks failed
failed=0

# 1. Code formatting check (Black)
if ! run_check "Code formatting (Black)" "uv run black --check --diff src/ tests/" "make format"; then
    failed=1
fi

# 2. Linting and import sorting check (ruff)
if ! run_check "Ruff linting and import sorting" "uv run ruff check src/ tests/" "make format"; then
    failed=1
fi

# 4. Type checking (mypy)
if ! run_check "Type checking (mypy)" "uv run mypy src/" "Fix the type issues above"; then
    failed=1
fi

# 5. Security check
if ! run_check "Security check" "python scripts/security_check.py" "Fix security issues above"; then
    failed=1
fi

# 5. Test execution (optional, can be disabled for faster commits)
# Uncomment the following lines if you want to run tests on every commit
# if ! run_check "Unit tests" "uv run pytest tests/" "Fix failing tests"; then
#     failed=1
# fi

# Final result
if [ $failed -eq 1 ]; then
    echo ""
    echo "${RED}❌ Pre-commit checks failed. Commit aborted.${NC}"
    echo "${YELLOW}💡 Run 'make check' to see all issues, or 'make format' to auto-fix formatting.${NC}"
    exit 1
else
    echo ""
    echo "${GREEN}🎉 All pre-commit checks passed! Commit proceeding...${NC}"
    exit 0
fi
"""

    # Check if we're in a git repository
    git_dir = Path(".git")
    if not git_dir.exists():
        print("❌ Not a git repository. Please run this from the project root.")
        return False

    # Create hooks directory if it doesn't exist
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    # Install pre-commit hook
    pre_commit_hook = hooks_dir / "pre-commit"

    # Backup existing hook if it exists
    if pre_commit_hook.exists():
        backup_file = hooks_dir / "pre-commit.backup"
        shutil.copy2(pre_commit_hook, backup_file)
        print(f"📋 Existing pre-commit hook backed up to {backup_file}")

    # Write the new hook
    pre_commit_hook.write_text(hook_content)

    # Make it executable
    pre_commit_hook.chmod(pre_commit_hook.stat().st_mode | stat.S_IEXEC)

    print("✅ Pre-commit hook installed successfully!")
    return True


def install_commit_msg_hook():
    """Install the commit-msg hook for commit message formatting."""
    hook_content = """#!/bin/sh
# Good Morning Agent commit-msg hook
# This script ensures commit messages follow conventional commit format

commit_regex='^(feat|fix|docs|style|refactor|test|chore)(\\(.+\\))?: .{1,50}'

if ! grep -qE "$commit_regex" "$1"; then
    echo "❌ Invalid commit message format!"
    echo ""
    echo "Commit messages should follow the conventional commit format:"
    echo "  <type>[optional scope]: <description>"
    echo ""
    echo "Examples:"
    echo "  feat: add newsletter collection module"
    echo "  fix(email): resolve IMAP connection issue"
    echo "  docs: update README installation steps"
    echo ""
    echo "Types: feat, fix, docs, style, refactor, test, chore"
    exit 1
fi
"""

    git_dir = Path(".git")
    hooks_dir = git_dir / "hooks"
    commit_msg_hook = hooks_dir / "commit-msg"

    # Backup existing hook if it exists
    if commit_msg_hook.exists():
        backup_file = hooks_dir / "commit-msg.backup"
        shutil.copy2(commit_msg_hook, backup_file)
        print(f"📋 Existing commit-msg hook backed up to {backup_file}")

    # Write the new hook
    commit_msg_hook.write_text(hook_content)

    # Make it executable
    commit_msg_hook.chmod(commit_msg_hook.stat().st_mode | stat.S_IEXEC)

    print("✅ Commit-msg hook installed successfully!")
    return True


def main():
    """Main function to install all hooks."""
    print("🪝 Installing Git hooks for Good Morning Agent...")
    print("=" * 50)

    success = True

    # Install pre-commit hook
    if not install_pre_commit_hook():
        success = False

    # Install commit-msg hook
    if not install_commit_msg_hook():
        success = False

    if success:
        print("")
        print("🎉 All Git hooks installed successfully!")
        print("")
        print("What this means:")
        print("• Every commit will run code quality checks")
        print("• Commit messages must follow conventional format")
        print("• Code must pass black, ruff, and mypy")
        print("")
        print("To bypass hooks (not recommended):")
        print("  git commit --no-verify")
        print("")
        print("To test the hooks:")
        print("  make check  # Run all quality checks manually")
    else:
        print("❌ Failed to install some hooks")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
