"""
Environment configuration management for Good Morning Agent.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.config import Config, load_config, setup_logging, validate_config


class EnvironmentManager:
    """Manages configuration loading for different environments."""

    ENV_FILE_MAP = {
        "production": "config/.env",
        "dev": "config/.env.dev",
        "test": "config/.env.test",
    }

    def load_config(self, env: str) -> Config:
        """Load configuration for the specified environment."""
        if env not in self.ENV_FILE_MAP:
            raise ValueError(
                f"Unknown environment: {env}. "
                f"Available: {', '.join(self.ENV_FILE_MAP.keys())}"
            )

        env_file = self.ENV_FILE_MAP[env]
        env_path = Path(env_file)

        # Check if environment file exists
        if not env_path.exists():
            # For dev and test, try to create from example if it doesn't exist
            if env in ["dev", "test"]:
                example_file = Path("config/.env.example")
                if example_file.exists():
                    print(f"⚠️  {env_file} not found, creating from example...")
                    env_path.write_text(example_file.read_text())
                else:
                    raise FileNotFoundError(
                        f"Environment file {env_file} not found and no example file available. "
                        f"Please create {env_file} with your configuration."
                    )
            else:
                raise FileNotFoundError(f"Environment file {env_file} not found")

        # Load configuration directly from the specific environment file
        config = load_config(str(env_path))
        validate_config(config)
        setup_logging(config)
        return config
