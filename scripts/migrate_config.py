#!/usr/bin/env python3
"""
Migration script to move configuration from .env to config.toml.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from openfatture.cli.wizard import save_config
from openfatture.utils.config import dirs, get_settings


def migrate():
    print("Loading settings from environment/.env...")
    settings = get_settings()

    config_path = Path(dirs.user_config_dir) / "config.toml"
    print(f"Target config file: {config_path}")

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    print("Saving configuration to TOML...")
    save_config(settings, config_path)

    print(f"✅ Successfully migrated configuration to {config_path}")
    print("You can now safely remove your .env file.")


if __name__ == "__main__":
    migrate()
