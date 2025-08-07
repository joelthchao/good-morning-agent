"""
Pipeline execution runner for Good Morning Agent.
"""

import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.email_reader import EmailReader
from processors.newsletter_processor import NewsletterProcessor
from senders.email_sender import EmailSender
from utils.config import Config


class PipelineRunner:
    """Executes the Good Morning Agent pipeline with configurable steps."""

    def __init__(self) -> None:
        self.email_reader: EmailReader | None = None
        self.processor: NewsletterProcessor | None = None
        self.email_sender: EmailSender | None = None

    def _initialize_components(self, config: Config) -> None:
        """Initialize pipeline components based on configuration."""
        self.email_reader = EmailReader(
            imap_server=config.email.imap_server,
            imap_port=config.email.imap_port,
            email_address=config.email.address,
            password=config.email.password,
        )

        self.processor = NewsletterProcessor(config)
        self.email_sender = EmailSender(config.email)

    def run_pipeline(
        self,
        config: Config,
        steps: list[str],
        limit: int | None = None,
        days: int = 7,
        send_email: bool = True,
        output_dir: Path = Path("output_samples"),
        verbose: bool = False,
        dry_run: bool = False,
    ) -> bool:
        """
        Run the Good Morning Agent pipeline with specified steps.

        Args:
            config: Configuration object
            steps: List of steps to execute ('collect', 'process', 'send')
            limit: Maximum number of emails to process
            days: Number of days to look back for emails
            send_email: Whether to actually send emails
            output_dir: Directory to save output files
            verbose: Enable verbose output
            dry_run: Simulate execution without making changes

        Returns:
            True if successful, False otherwise
        """
        if dry_run:
            print("🔍 DRY RUN MODE - No actual operations will be performed")
            print()

        if verbose:
            print("🚀 Starting Good Morning Agent Pipeline")
            print("=" * 50)

        try:
            self._initialize_components(config)

            newsletters = None
            processing_result = None

            # Step 1: Collect emails
            if "collect" in steps:
                if verbose:
                    print("📧 Step 1: Collecting newsletters...")

                if not dry_run:
                    assert self.email_reader is not None
                    self.email_reader.connect()
                    newsletters = self.email_reader.get_recent_newsletters_as_content(
                        days=days, limit=limit
                    )

                    if verbose:
                        print(f"✅ Found {len(newsletters)} newsletters to process")
                        for i, newsletter in enumerate(newsletters[:5], 1):
                            print(
                                f"  {i}. {newsletter.source} - {newsletter.title[:60]}..."
                            )
                        if len(newsletters) > 5:
                            print(f"  ... and {len(newsletters) - 5} more")
                else:
                    print("  📋 Would collect recent newsletters")

                if newsletters is not None and len(newsletters) == 0:
                    print(f"⚠️  No newsletters found in the last {days} days")
                    return True

            # Step 2: Process with AI
            if "process" in steps:
                if verbose:
                    print("\n🤖 Step 2: Processing newsletters with AI...")

                if newsletters is None:
                    print(
                        "⚠️  No newsletters to process. Run 'collect' step first or use 'all' steps."
                    )
                    return False

                if not dry_run:
                    assert self.processor is not None
                    processing_result = self.processor.process_newsletters(newsletters)

                    if not processing_result.success:
                        print(
                            f"❌ Failed to process newsletters: {processing_result.errors}"
                        )
                        return False

                    if verbose:
                        print("✅ AI processing completed successfully")
                        print(f"  - Processed: {processing_result.processed_count}")
                        print(f"  - Failed: {processing_result.failed_count}")
                        email_data = processing_result.email_data
                        print(f"  - Subject: {email_data.subject}")
                        print(
                            f"  - Content length: {len(email_data.content)} characters"
                        )
                        if email_data.html_content:
                            print(
                                f"  - HTML content: {len(email_data.html_content)} characters"
                            )
                else:
                    print(
                        f"  📋 Would process {len(newsletters) if newsletters else 'N'} newsletters with AI"
                    )

            # Step 3: Send email or save to file
            if "send" in steps:
                if processing_result is None:
                    print(
                        "⚠️  No processed content to send. Run 'process' step first or use 'all' steps."
                    )
                    return False

                email_data = processing_result.email_data

                if send_email and not dry_run:
                    if verbose:
                        print(
                            f"\n📤 Step 3: Sending email to {email_data.recipient}..."
                        )

                    assert self.email_sender is not None
                    success = self.email_sender.send_email(email_data)
                    if success:
                        print("✅ Email sent successfully!")
                        print(f"📧 Check your inbox at: {email_data.recipient}")
                    else:
                        print("❌ Failed to send email")
                        return False
                else:
                    if verbose:
                        print("\n💾 Step 3: Saving content to files...")

                    if not dry_run:
                        # Save to output files
                        output_dir.mkdir(exist_ok=True)

                        current_date = datetime.now()
                        timestamp = current_date.strftime("%Y%m%d_%H%M%S")

                        # Save HTML if available
                        if email_data.html_content:
                            html_file = output_dir / f"pipeline_output_{timestamp}.html"
                            html_file.write_text(
                                email_data.html_content, encoding="utf-8"
                            )
                            print(f"✅ HTML saved: {html_file}")

                        # Save plain text
                        txt_file = output_dir / f"pipeline_output_{timestamp}.txt"
                        txt_file.write_text(email_data.content, encoding="utf-8")
                        print(f"✅ Text saved: {txt_file}")
                    else:
                        print(f"  📋 Would save content to {output_dir}")

            if verbose:
                print("\n🎉 Pipeline execution completed!")
                print("=" * 50)

            return True

        except Exception as e:
            print(f"❌ Pipeline error: {str(e)}")
            if verbose:
                import traceback

                traceback.print_exc()
            return False

        finally:
            # Clean up connections
            try:
                if self.email_reader:
                    self.email_reader.disconnect()
            except Exception:
                pass
