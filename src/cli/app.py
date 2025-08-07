"""
Main CLI application for Good Morning Agent.
"""

import argparse
import sys
from pathlib import Path

from .config import EnvironmentManager
from .runner import PipelineRunner


class GoodMorningApp:
    """Main CLI application class."""

    def __init__(self) -> None:
        self.env_manager = EnvironmentManager()
        self.runner = PipelineRunner()

    def create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            description="Good Morning Agent - AI-powered newsletter digest generator",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python -m src.main --env production                    # Full production run
  python -m src.main --env dev --no-send                # Dev run without sending
  python -m src.main --env test --steps collect,process # Only collect and process
  python -m src.main --env dev --limit 5 --verbose      # Dev run with 5 emails, verbose
            """,
        )

        # Environment control
        parser.add_argument(
            "--env",
            choices=["production", "dev", "test"],
            default="dev",
            help="Environment to use (default: dev)",
        )

        # Execution steps control
        parser.add_argument(
            "--steps",
            default="all",
            help="Steps to execute: collect,process,send or 'all' (default: all)",
        )

        # Behavior control
        parser.add_argument(
            "--no-send",
            action="store_true",
            help="Don't actually send email, save to file instead",
        )

        parser.add_argument(
            "--limit",
            type=int,
            help="Limit number of emails to process (default: no limit)",
        )

        parser.add_argument(
            "--days",
            type=int,
            default=7,
            help="Number of days to look back for emails (default: 7)",
        )

        parser.add_argument(
            "--output-dir",
            type=Path,
            default=Path("output_samples"),
            help="Output directory for saved files (default: output_samples/)",
        )

        # Debug and development
        parser.add_argument(
            "--verbose", action="store_true", help="Enable verbose output"
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate execution without making actual changes",
        )

        return parser

    def parse_steps(self, steps_str: str) -> list[str]:
        """Parse and validate the steps argument."""
        if steps_str.lower() == "all":
            return ["collect", "process", "send"]

        steps = [s.strip().lower() for s in steps_str.split(",")]
        valid_steps = {"collect", "process", "send"}

        invalid_steps = set(steps) - valid_steps
        if invalid_steps:
            raise ValueError(
                f"Invalid steps: {', '.join(invalid_steps)}. "
                f"Valid steps are: {', '.join(valid_steps)}"
            )

        return steps

    def run(self, args: list[str] | None = None) -> int:
        """Run the application with given arguments."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        try:
            # Parse steps
            steps = self.parse_steps(parsed_args.steps)

            # Load environment configuration
            config = self.env_manager.load_config(parsed_args.env)

            if parsed_args.verbose:
                print(f"🔧 Environment: {parsed_args.env}")
                print(f"📋 Steps: {' → '.join(steps)}")
                print(f"📧 Email: {config.email.address}")
                if parsed_args.no_send:
                    print("📤 Send mode: Save to file only")
                if parsed_args.limit:
                    print(f"📊 Limit: {parsed_args.limit} emails")
                print(f"📅 Days back: {parsed_args.days}")
                print()

            # Create output directory if needed
            if parsed_args.no_send or "send" not in steps:
                parsed_args.output_dir.mkdir(exist_ok=True)

            # Execute pipeline
            success = self.runner.run_pipeline(
                config=config,
                steps=steps,
                limit=parsed_args.limit,
                days=parsed_args.days,
                send_email=not parsed_args.no_send,
                output_dir=parsed_args.output_dir,
                verbose=parsed_args.verbose,
                dry_run=parsed_args.dry_run,
            )

            return 0 if success else 1

        except Exception as e:
            print(f"❌ Error: {e}", file=sys.stderr)
            if parsed_args.verbose:
                import traceback

                traceback.print_exc()
            return 1
