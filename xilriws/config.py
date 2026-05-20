from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


class GeneralConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 5090


class DevConfig(BaseModel):
    proxy_path: str = "/xilriws/xilriws-proxy"
    targetfp_path: str = "/xilriws/xilriws-targetfp"
    proxies_list_path: str = "/xilriws/proxies.txt"
    log_level: str = "INFO"
    headless_browser: bool = True


class AppConfig(BaseModel):
    general: GeneralConfig = Field(default_factory=GeneralConfig)
    dev: DevConfig = Field(default_factory=DevConfig)


def load_config(path: str | Path = "config.toml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        return AppConfig()

    with config_path.open("rb") as config_file:
        data: dict[str, Any] = tomllib.load(config_file)

    return AppConfig.model_validate(data)


config = load_config()
