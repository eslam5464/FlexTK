import json
import tomllib
from pathlib import Path
from typing import Any

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


def save_config(config: dict[str, Any]):
    if not settings.config_directory.exists():
        settings.config_directory.mkdir(parents=True, exist_ok=True)

    with open(settings.config_file_path, "w") as file:
        json.dump(config, file, indent=4)


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    config_path = settings.config_file_path if config_path is None else config_path

    if not config_path.exists():
        return {}

    if not config_path.exists():
        config_path.mkdir(parents=True, exist_ok=True)

    with open(config_path, "r") as file:
        return json.load(file)


settings = Settings()
