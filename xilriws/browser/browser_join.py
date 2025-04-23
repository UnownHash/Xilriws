from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass

import nodriver
from loguru import logger

from xilriws.constants import JOIN_URL
from xilriws.debug import IS_DEBUG
from xilriws.extension_comm import FINISH_PROXY
from xilriws.js import load, recaptcha
from xilriws.ptc_auth import LoginException
from .browser import Browser, ProxyException
from xilriws.ptc import ptc_utils
from xilriws.extension_comm import FINISH_PROXY, FINISH_COOKIE_PURGE
from xilriws.proxy import Proxy


logger = logger.bind(name="Browser")


@dataclass
class CionResponse:
    reese_cookie: dict
    create_tokens: list[str]
    activate_tokens: list[str]
    timestamp: int
    proxy: str


class BrowserJoin(Browser):
    async def get_join_tokens(self, proxy: Proxy) -> CionResponse | None:
        try:
            await self.start_browser()
        except Exception:
            return None

        try:
            timestamp = int(time.time())
            js_future, js_check_handler = await self.get_js_check_handler(JOIN_URL)
            cookie_future = await self.ext_comm.add_listener(FINISH_COOKIE_PURGE)

            await self.new_tab()

            proxy_future = await self.ext_comm.add_listener(FINISH_PROXY)

            await self.ext_comm.send(
                "setProxy",
                {
                    "host": proxy.host,
                    "port": proxy.port,
                    "scheme": proxy.scheme,
                    "password": proxy.password,
                    "username": proxy.username,
                }
            )

            try:
                await asyncio.wait_for(proxy_future, 2)
            except asyncio.TimeoutError:
                logger.info("Didn't get confirmation that proxy changed, continuing anyway")

            if not self.first_run and cookie_future and not cookie_future.done():
                try:
                    await asyncio.wait_for(cookie_future, 2)
                except asyncio.TimeoutError:
                    logger.info("Didn't get confirmation that cookies were cleared, continuing anyway")

            self.first_run = False

            self.tab.add_handler(nodriver.cdp.network.ResponseReceived, js_check_handler)
            logger.info("Opening Join page")
            await self.tab.get(url=JOIN_URL)

            html = await self.tab.get_content()
            if "neterror" in html.lower():
                raise ProxyException(f"Page couldn't be reached (Proxy: {proxy.url})")

            try:
                await asyncio.wait_for(js_future, timeout=100)
                self.tab.handlers.clear()
                logger.info("JS check done. reloading")
            except asyncio.TimeoutError:
                raise LoginException("Timeout on JS challenge")

            await self.tab.reload()

            logger.debug("Waiting for imperva or recaptcha iframe")
            found_captcha = False
            found_error = False
            loop = asyncio.get_running_loop()
            start_time = loop.time()
            while not found_captcha and not found_error and start_time + 100 > loop.time():
                found_captcha = await self.tab.query_selector("iframe[title='reCAPTCHA']")
                found_error = await self.tab.query_selector("iframe#main-iframe")

            if found_error:
                # TODO check for error 16, mark proxies as dead
                imp_code, imp_reason = ptc_utils.get_imperva_error_code(await self.tab.get_content())
                raise LoginException(f"Error code {imp_code} ({imp_reason}) with Proxy ({proxy.url})")

            if not found_captcha:
                raise LoginException("Timeout waiting for captcha")

            obj, error = await self.tab.send(nodriver.cdp.runtime.evaluate(recaptcha.SRC))

            logger.info("Preparing token retreiving")

            obj, errors = await self.tab.send(nodriver.cdp.runtime.evaluate(load.SRC))
            obj: nodriver.cdp.runtime.RemoteObject

            logger.info("Getting captcha tokens")
            r, errors = await self.tab.send(nodriver.cdp.runtime.await_promise(obj.object_id, return_by_value=True))

            logger.info("Getting cookies from browser")
            all_cookies = await self.get_cookies()
            recaptcha_tokens = r.value

            self.consecutive_failures = 0

            return CionResponse(
                reese_cookie=all_cookies,
                create_tokens=recaptcha_tokens["create"],
                activate_tokens=recaptcha_tokens["activate"],
                timestamp=timestamp,
                proxy=proxy.full_url.geturl(),
            )
        except LoginException as e:
            logger.error(f"{str(e)} while getting tokens")
            self.consecutive_failures += 1
            await asyncio.sleep(1)
            return None
        except ProxyException as e:
            proxy.invalidate()
            logger.error(f"{str(e)} while getting tokens")
            await self.stop_browser()
            return None
        except Exception as e:
            logger.exception("Exception during browser", e)

        logger.error("Error while getting cookie from browser, it will be restarted next time")
        await self.stop_browser()
        return None
