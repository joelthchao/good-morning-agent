#!/usr/bin/env python3
"""
Test execution script for Good Morning Agent.

This script provides different testing modes:
- Unit tests only (fast)
- Integration tests (requires test credentials)
- End-to-end tests (requires real services)
- All tests with coverage reporting

Usage:
    python tests/run_tests.py --unit
    python tests/run_tests.py --integration
    python tests/run_tests.py --e2e
    python tests/run_tests.py --all
    python tests/run_tests.py --coverage
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False


def check_test_requirements() -> bool:
    """Check if test requirements are installed."""
    try:
        import pytest
        import pytest_cov
        import pytest_mock

        return True
    except ImportError as e:
        print(f"❌ Missing test dependencies: {e}")
        print("Run: uv sync --dev")
        return False


def run_unit_tests() -> bool:
    """Run unit tests only."""
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/unit/",
        "-v",
        "--tb=short",
        "-m",
        "not slow",
    ]
    return run_command(cmd, "Unit tests")


def run_integration_tests() -> bool:
    """Run integration tests."""
    # Check for integration test requirements
    required_vars = [
        "INTEGRATION_COLLECTION_EMAIL",
        "INTEGRATION_EMAIL_PASSWORD",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("⚠️  Integration tests skipped - missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("Set these variables to run integration tests")
        return True  # Don't fail if integration tests are skipped

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/integration/",
        "-v",
        "--tb=short",
        "-m",
        "integration",
    ]
    return run_command(cmd, "Integration tests")


def run_e2e_tests() -> bool:
    """Run end-to-end tests."""
    # Check for E2E test requirements
    required_vars = [
        "INTEGRATION_COLLECTION_EMAIL",
        "INTEGRATION_EMAIL_PASSWORD",
        "INTEGRATION_OPENAI_API_KEY",
        "INTEGRATION_SENDER_EMAIL",
        "INTEGRATION_SENDER_PASSWORD",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print("⚠️  E2E tests skipped - missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("Set these variables to run E2E tests")
        return True  # Don't fail if E2E tests are skipped

    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/e2e/",
        "-v",
        "--tb=short",
        "-m",
        "e2e",
        "-s",  # Don't capture output for E2E tests
    ]
    return run_command(cmd, "End-to-end tests")


def run_all_tests() -> bool:
    """Run all test suites."""
    success = True
    success &= run_unit_tests()
    success &= run_integration_tests()
    success &= run_e2e_tests()
    return success


def run_tests_with_coverage() -> bool:
    """Run tests with coverage reporting."""
    cmd = [
        "python",
        "-m",
        "pytest",
        "tests/",
        "--cov=src",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "--cov-fail-under=80",
        "-v",
    ]

    success = run_command(cmd, "Tests with coverage")

    if success:
        print("\n📊 Coverage report generated in htmlcov/index.html")

    return success


def run_linting() -> bool:
    """Run code quality checks."""
    checks = [
        (
            ["python", "-m", "black", "--check", "src/", "tests/"],
            "Black formatting check",
        ),
        (
            ["python", "-m", "ruff", "check", "src/", "tests/"],
            "Ruff linting and import sorting",
        ),
        (["python", "-m", "mypy", "src/"], "MyPy type checking"),
    ]

    success = True
    for cmd, description in checks:
        success &= run_command(cmd, description)

    return success


def main():
    """Main test execution function."""
    parser = argparse.ArgumentParser(description="Run Good Morning Agent tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests"
    )
    parser.add_argument("--e2e", action="store_true", help="Run end-to-end tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument(
        "--coverage", action="store_true", help="Run tests with coverage"
    )
    parser.add_argument("--lint", action="store_true", help="Run linting checks")

    args = parser.parse_args()

    # Check requirements
    if not check_test_requirements():
        sys.exit(1)

    print("🚀 Good Morning Agent - Test Runner")
    print("=" * 50)

    success = True

    if args.unit or (
        not any([args.integration, args.e2e, args.all, args.coverage, args.lint])
    ):
        success &= run_unit_tests()

    if args.integration:
        success &= run_integration_tests()

    if args.e2e:
        success &= run_e2e_tests()

    if args.all:
        success &= run_all_tests()

    if args.coverage:
        success &= run_tests_with_coverage()

    if args.lint:
        success &= run_linting()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
