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
    model_config = ConfigDict(extra="allow")

    host: str = "0.0.0.0"
    port: int = 5090


class DevConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    proxy_path: str = "/xilriws/xilriws-proxy"
    targetfp_path: str = "/xilriws/xilriws-targetfp"
    proxies_list_path: str = "/xilriws/proxies.txt"
    chrome_path: str | None = None
    log_level: str = "INFO"
    headless_browser: bool = True


class AuthConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    cookie_max_uses: int = 7
    cookie_storage_size: int = 2
    max_auth_attempts: int = 3


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    general: GeneralConfig = Field(default_factory=GeneralConfig)
    dev: DevConfig = Field(default_factory=DevConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)


def load_config(path: str | Path = "config.toml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        return AppConfig()

    with config_path.open("rb") as config_file:
        data: dict[str, Any] = tomllib.load(config_file)

    return AppConfig.model_validate(data)


config = load_config()
