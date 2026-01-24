"""
Configuration management - loading, saving, and accessing app settings.
"""

import os
import sys
import json
from pathlib import Path
from typing import Any

try:
    from core.constants import DEFAULT_CONFIG
except ImportError:
    from .constants import DEFAULT_CONFIG


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent.parent
    return base_path / "bg_remover_config.json"


def load_config() -> dict:
    """Load configuration from file, merging with defaults."""
    config_path = get_config_path()
    config = DEFAULT_CONFIG.copy()

    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                saved = json.load(f)
                config.update(saved)
        except Exception:
            pass

    return config


def save_config(config: dict) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception:
        pass


def get_hf_token() -> str:
    """Get Hugging Face token from config or environment."""
    # Check environment variable first
    token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
    if token:
        return token

    # Check config file
    config = load_config()
    return config.get("hf_token", "")


def set_hf_token(token: str) -> None:
    """Set Hugging Face token in config and environment."""
    if token:
        os.environ["HF_TOKEN"] = token
        # Also try to login via huggingface_hub if available
        try:
            from huggingface_hub import login
            login(token=token, add_to_git_credential=False)
        except Exception:
            pass
