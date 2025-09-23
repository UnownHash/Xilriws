from __future__ import annotations

import time
from copy import copy
from typing import TYPE_CHECKING
from urllib.parse import ParseResult, urlparse

from loguru import logger

if TYPE_CHECKING:
    from .extension_comm import ExtensionComm


PROXY_TIMEOUT = 60 * 60


class Proxy:
    def __init__(self, url: str | None):
        if isinstance(url, str):
            if "://" not in url:
                url = "http://" + url
            url = urlparse(url)
        elif url is None:
            url = urlparse(url)

        self.full_url: ParseResult = url

        self.host = url.hostname
        self.port = url.port
        self.scheme = url.scheme
        self.username = url.username
        self.password = url.password

        self.last_limited: float = 0
        self.invalidated: bool = False

    @property
    def url(self):
        return f"{self.host}:{self.port}"

    def is_good(self):
        return not self.invalidated and self.last_limited + PROXY_TIMEOUT < time.time()

    def rate_limited(self):
        self.last_limited = time.time()

    def invalidate(self):
        self.invalidated = True


logger = logger.bind(name="Proxy")


class ProxyDistributor:
    def __init__(self, ext_comm: ExtensionComm):
        self.next_proxy: Proxy | None = None
        self.current_proxy: Proxy | None = None
        self.ext_comm = ext_comm

    def set_next_proxy(self, proxy: Proxy) -> bool:
        if self.current_proxy and self.current_proxy.full_url.geturl() == proxy.full_url.geturl():
            return False

        self.next_proxy = proxy
        return True

    async def change_proxy(self, proxy: Proxy | None = None) -> bool:
        if proxy is not None:
            self.set_next_proxy(proxy)

        if self.next_proxy is not None:
            self.current_proxy = copy(self.next_proxy)

        if self.current_proxy is None:
            return False

        if not self.current_proxy.host:
            return False

        logger.info(f"Switching to Proxy {self.current_proxy.host}:{self.current_proxy.port}")

        await self.ext_comm.send(
            "setProxy",
            {
                "host": self.current_proxy.host,
                "port": self.current_proxy.port,
                "scheme": self.current_proxy.scheme,
                "password": self.current_proxy.password,
                "username": self.current_proxy.username,
            }
        )
        return True
