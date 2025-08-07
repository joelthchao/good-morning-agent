"""
Main entry point for Good Morning Agent CLI application.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from cli import GoodMorningApp


def main() -> int:
    """Main entry point function."""
    app = GoodMorningApp()
    exit_code: int = app.run()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
