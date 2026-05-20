from __future__ import annotations

from .proxy import Proxy, ProxyDistributor
from loguru import logger
import asyncio

from xilriws.config import config

logger = logger.bind(name="Proxy Dispenser")


class ProxyDispenser:
    def __init__(self, list_path: str):
        self.proxies: list[Proxy] = []
        with open(list_path, "r") as f:
            for proxy_url in f.readlines():
                if not proxy_url:
                    continue

                proxy_url = proxy_url.strip()

                if proxy_url.lower() == "local":
                    proxy_url = None

                try:
                    self.proxies.append(Proxy(proxy_url))
                except Exception as e:
                    logger.error(f"There was a problem parsing proxy {proxy_url}: {str(e)}")

        if not self.proxies:
            logger.warning("No configured proxies! Using local IP only")
            self.proxies.append(Proxy(None))

        self.current_auth_index = 0
        self.current_proxy_uses = 0

    async def get_auth_proxy(self) -> Proxy:
        self.current_proxy_uses += 1
        if self.current_proxy_uses > config.auth.proxy.max_uses_before_rotation:
            self.current_auth_index = (self.current_auth_index + 1) % len(self.proxies)
            self.current_proxy_uses = 0

        while True:
            for i, proxy in enumerate(self.proxies):
                if i >= self.current_auth_index and proxy.is_good():
                    return proxy

            logger.error("No free Proxies!")
            self.current_auth_index = 0
            self.current_proxy_uses = 0
            await asyncio.sleep(5)
