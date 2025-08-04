#!/usr/bin/env python3
"""
Security Check Script for Good Morning Agent.

This script checks for potential security issues before committing code.
"""

import re
import subprocess
from pathlib import Path


def check_sensitive_files():
    """Check for sensitive files that might be committed."""
    print("🔍 Checking for sensitive files...")

    sensitive_patterns = [
        r"\.env$",
        r"\.env\.",
        r"\.key$",
        r"\.pem$",
        r"credentials\.json$",
        r"password",
        r"secret",
    ]

    # Get files staged for commit
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        staged_files = (
            result.stdout.strip().split("\n") if result.stdout.strip() else []
        )
    except subprocess.CalledProcessError:
        staged_files = []

    # Check staged files
    issues = []
    for file in staged_files:
        if not file:
            continue

        for pattern in sensitive_patterns:
            if re.search(pattern, file, re.IGNORECASE):
                issues.append(f"Staged file might be sensitive: {file}")

    return issues


def check_file_contents():
    """Check file contents for potential secrets."""
    print("🔍 Checking file contents for secrets...")

    secret_patterns = [
        (r'password\s*=\s*["\'][^"\']+["\']', "Password in code"),
        (r'api_key\s*=\s*["\'][^"\']+["\']', "API key in code"),
        (r"sk-[a-zA-Z0-9]{48}", "OpenAI API key"),
        (r"[a-zA-Z0-9]{16}", "Potential app password (16 chars)"),
        (r"@gmail\.com.*[a-zA-Z0-9]{16}", "Gmail credentials"),
    ]

    issues = []

    # Get staged files content
    try:
        result = subprocess.run(
            ["git", "diff", "--cached"], capture_output=True, text=True, check=True
        )
        diff_content = result.stdout
    except subprocess.CalledProcessError:
        return issues

    # Check for secrets in diff
    for pattern, description in secret_patterns:
        if re.search(pattern, diff_content, re.IGNORECASE):
            # Skip if it's in a template or example file
            if not any(
                keyword in diff_content for keyword in ["example", "template", "your-"]
            ):
                issues.append(f"{description} found in staged changes")

    return issues


def check_gitignore():
    """Verify .gitignore covers sensitive files."""
    print("🔍 Checking .gitignore coverage...")

    gitignore_path = Path(".gitignore")
    if not gitignore_path.exists():
        return ["No .gitignore file found"]

    content = gitignore_path.read_text()

    required_patterns = [
        ".env",
        "config/.env",
        "*.key",
        "credentials.json",
    ]

    issues = []
    for pattern in required_patterns:
        if pattern not in content:
            issues.append(f"Missing .gitignore pattern: {pattern}")

    return issues


def run_security_check():
    """Run comprehensive security check."""
    print("🔒 Good Morning Agent - Security Check")
    print("=" * 45)
    print()

    all_issues = []

    # Check sensitive files
    issues = check_sensitive_files()
    all_issues.extend(issues)

    # Check file contents
    issues = check_file_contents()
    all_issues.extend(issues)

    # Check .gitignore
    issues = check_gitignore()
    all_issues.extend(issues)

    # Report results
    if all_issues:
        print("❌ Security issues found:")
        for issue in all_issues:
            print(f"   • {issue}")
        print()
        print("🛡️  Please fix these issues before committing!")
        return False
    else:
        print("✅ No security issues found!")
        print("✅ Safe to commit")
        return True


def main():
    """Main function."""
    success = run_security_check()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
