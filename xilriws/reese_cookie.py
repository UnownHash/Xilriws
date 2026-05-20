from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from loguru import logger

from .config import config
from .constants import EXPIRATION
from .proxy import ProxyDistributor, Proxy
from .proxy_dispenser import ProxyDispenser
from .task_creator import task_creator, AwaitableSet

if TYPE_CHECKING:
    from .browser.browser_auth import BrowserAuth

logger = logger.bind(name="Cookie")


class ReeseCookie:
    def __init__(self, cookies: dict[str, str], proxy: Proxy):
        self.value: str = "value"
        self.expiration: float = time.time() + EXPIRATION
        self.uses: int = 0
        self.cookies = cookies
        self.proxy = proxy

    def is_good(self) -> bool:
        return time.time() < self.expiration and self.uses < config.auth.cookie_max_uses

    def use(self) -> None:
        self.uses += 1


class CookieMonster:
    fill_event: asyncio.Event

    def __init__(self, browser: BrowserAuth, proxies: ProxyDistributor, proxy_dispenser: ProxyDispenser):
        self.browser: BrowserAuth = browser
        self.cookies: AwaitableSet[ReeseCookie] = AwaitableSet()
        self.proxies = proxies
        self.proxy_dispenser = proxy_dispenser

    async def prepare(self):
        self.fill_event = asyncio.Event()
        task_creator.create_task(self.fill_task())
        self.fill_event.set()

    async def get_reese_cookie(self) -> ReeseCookie:
        logger.info("Getting a reese cookie from storage")
        cookie: ReeseCookie | None = None

        while not cookie:
            possible_cookie = await self.get_next_cookie()
            if not possible_cookie.is_good():
                await self.cookies.remove(possible_cookie)
                self.fill_event.set()
            else:
                cookie = possible_cookie

        cookie.use()
        logger.info("Cookie selected")

        return cookie

    async def remove_cookie(self, cookie: ReeseCookie) -> None:
        await self.cookies.remove(cookie)
        self.fill_event.set()

    async def fill_task(self):
        while True:
            await self.fill_event.wait()
            logger.info("Filling cookie storage in the background")

            try:
                while len(self.cookies) < config.auth.cookie_storage_size:
                    await self.__get_one_cookie()
                    logger.info(f"Cookie storage at {len(self.cookies)}/{config.auth.cookie_storage_size}")
            except Exception as e:
                logger.exception("unhandled exception while filling cookie storage, please report", e)

            self.fill_event.clear()

    async def get_next_cookie(self) -> ReeseCookie:
        async with self.cookies.cond:
            while not len(self.cookies):
                await self.cookies.cond.wait()

            next_cookie: ReeseCookie | None = None
            for potential_cookie in self.cookies.set:
                if next_cookie is None:
                    next_cookie = potential_cookie
                elif potential_cookie.expiration < next_cookie.expiration:
                    next_cookie = potential_cookie

            return next_cookie

    async def __get_one_cookie(self) -> ReeseCookie | None:
        logger.info("Opening browser to get a cookie")
        proxy = await self.proxy_dispenser.get_auth_proxy()
        proxy_changed = self.proxies.set_next_proxy(proxy)

        cookie = await self.browser.get_reese_cookie(proxy_changed)

        if not cookie:
            return None

        await self.cookies.add(cookie)
        return cookie
