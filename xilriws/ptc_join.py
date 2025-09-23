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
    def __init__(self, browser: BrowserJoin):
        self.browser = browser
        self.responses: list[CionResponse] = []
        self.last_cion_call = time()
        self.is_running = False

    async def get_join_tokens(self, proxy: str | None) -> CionResponse | None:
        self.is_running = True

        try:
            logger.info(f"Getting cion tokens using proxy {proxy}")
            resp = await self.browser.get_join_tokens(Proxy(proxy))
            self.is_running = False
            return resp
        except Exception as e:
            logger.exception("unhandled exception while getting tokens", e)

        self.is_running = False
