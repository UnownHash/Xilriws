from __future__ import annotations
from .browser import Browser, CionResponse, BrowserJoin
from .task_creator import task_creator
from loguru import logger
import asyncio
from .proxy_dispenser import ProxyDispenser
from .proxy import ProxyDistributor, Proxy
from time import time

logger = logger.bind(name="Tokens")


class PtcJoin:
    def __init__(self, browser: BrowserJoin, proxies: ProxyDistributor, proxy_dispenser: ProxyDispenser):
        self.browser = browser
        self.responses: list[CionResponse] = []
        self.proxies = proxies
        self.proxy_dispenser = proxy_dispenser
        self.last_cion_call = time()

    async def get_join_tokens(self, proxy: str | None) -> CionResponse | None:
        try:
            logger.info(f"Getting cion tokens using proxy {proxy}")
            return await self.browser.get_join_tokens(Proxy(proxy))
        except Exception as e:
            logger.exception("unhandled exception while getting tokens", e)

    async def prepare(self):
        task_creator.create_task(self.fill_task())

    async def fill_task(self):
        # TODO: invalidate old tokens
        while True:
            if self.last_cion_call < time() - 30:
                logger.warning("Cion doesn't seem to be running! Pausing Cion-Xilriws")
                await asyncio.sleep(5)
                continue

            logger.info("Getting tokens")
            try:
                proxy = await self.proxy_dispenser.get_auth_proxy()
                proxy.rate_limited()
                proxy_changed = self.proxies.set_next_proxy(proxy)
                resp = await self.browser.get_join_tokens(proxy_changed)
                if resp:
                    self.responses.append(resp)
            except Exception as e:
                logger.exception("unhandled exception while getting tokens", e)
