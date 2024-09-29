import json
import sys
import tomllib
from pathlib import Path
from typing import Any

import click
from core.schema import ClickColors
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).parent.parent

with open(PROJECT_DIR / "pyproject.toml", "rb") as f:
    PYPROJECT_CONTENT = tomllib.load(f)["tool"]["poetry"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    package_name: str = PYPROJECT_CONTENT["name"]
    package_version: str = PYPROJECT_CONTENT["version"]
    package_description: str = PYPROJECT_CONTENT["description"]

    config_directory: Path = Path.home() / ".config" / "flex_tk"
    config_file_path: Path = config_directory / "config.json"


def save_config(config: dict[str, Any]) -> None:
    """
    Saves the provided configuration dictionary to the specified config file path.
    :param config: The configuration data to be saved, represented as a dictionary.
    """
    if not settings.config_directory.exists():
        settings.config_directory.mkdir(parents=True, exist_ok=True)

    with open(settings.config_file_path, "w") as file:
        json.dump(config, file, indent=4)


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """
    Loads configuration from the specified JSON file. If the file doesn't exist, returns an empty dictionary.
    :param config_path: The path to the config file. If None, defaults to settings.config_file_path.
    :return: A dictionary containing the configuration data if successful, otherwise exits on error.
    """
    config_path = settings.config_file_path if config_path is None else config_path

    if not config_path.exists():
        return {}

    if not config_path.is_file():
        click.secho(message="The configuration file path is not a file", fg=ClickColors.red)
        sys.exit()

    if not str(config_path).lower().endswith(".json"):
        click.secho(message="The configuration must be a json file", fg=ClickColors.red)
        sys.exit()

    with open(config_path, "r") as config_file:
        return json.load(config_file)


settings = Settings()
