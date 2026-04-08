"""
EDAI4 - Helper Utilities
Common utility functions used across the application
"""

import os
import yaml
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_config(config_path: str | Path) -> dict[str, Any]:
    """
    Load YAML configuration file.

    Args:
        config_path: Path to YAML config file

    Returns:
        Dictionary with configuration values
    """
    config_path = Path(config_path)

    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logger.info(f"Loaded configuration from: {config_path}")
    return config


def load_env(env_path: str | Path | None = None) -> None:
    """
    Load environment variables from .env file.

    Args:
        env_path: Path to .env file (optional)
    """
    if env_path:
        load_dotenv(env_path)
    else:
        load_dotenv()

    logger.debug("Environment variables loaded")


def get_project_root() -> Path:
    """
    Get the project root directory.

    Returns:
        Path to project root
    """
    # Navigate up from this file to find project root
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "requirements.txt").exists():
            return parent
    return Path.cwd()


def ensure_directory(path: str | Path) -> Path:
    """
    Ensure a directory exists, create if it doesn't.

    Args:
        path: Directory path

    Returns:
        Path object
    """
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_file_extension(file_path: str | Path) -> str:
    """
    Get file extension (lowercase, with dot).

    Args:
        file_path: Path to file

    Returns:
        File extension (e.g., '.pdf', '.png')
    """
    return Path(file_path).suffix.lower()


def is_supported_format(file_path: str | Path, supported: list[str]) -> bool:
    """
    Check if file format is supported.

    Args:
        file_path: Path to file
        supported: List of supported extensions

    Returns:
        True if supported, False otherwise
    """
    ext = get_file_extension(file_path)
    return ext in [s.lower() for s in supported]


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    return filename


def generate_output_path(
    input_path: str | Path,
    output_dir: str | Path,
    suffix: str = "",
    extension: str = ".xlsx"
) -> Path:
    """
    Generate output file path based on input file.

    Args:
        input_path: Input file path
        output_dir: Output directory
        suffix: Suffix to add to filename
        extension: Output file extension

    Returns:
        Output file path
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)

    # Create output filename
    stem = input_path.stem
    if suffix:
        stem = f"{stem}_{suffix}"

    output_path = output_dir / f"{stem}{extension}"
    return output_path


class ConfigManager:
    """
    Centralized configuration manager for EDAI4.
    """

    _instance = None
    _config: dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, config_dir: str | Path | None = None) -> None:
        """
        Load all configuration files.

        Args:
            config_dir: Directory containing config files
        """
        if config_dir is None:
            config_dir = get_project_root() / "config"

        config_dir = Path(config_dir)

        # Load main settings
        settings_path = config_dir / "settings.yaml"
        if settings_path.exists():
            self._config["settings"] = load_config(settings_path)

        # Load instrument rules
        rules_path = config_dir / "instrument_rules.yaml"
        if rules_path.exists():
            self._config["instrument_rules"] = load_config(rules_path)

        # Load safety rules
        safety_path = config_dir / "safety_rules.yaml"
        if safety_path.exists():
            self._config["safety_rules"] = load_config(safety_path)

        # Load environment variables
        load_env()

        logger.info(f"Configuration loaded from: {config_dir}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Dot-notation key (e.g., 'settings.app.name')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_settings(self) -> dict[str, Any]:
        """Get all settings."""
        return self._config.get("settings", {})

    def get_instrument_rules(self) -> dict[str, Any]:
        """Get instrument rules."""
        return self._config.get("instrument_rules", {})

    def get_safety_rules(self) -> dict[str, Any]:
        """Get safety rules."""
        return self._config.get("safety_rules", {})


# Global config manager instance
config = ConfigManager()
