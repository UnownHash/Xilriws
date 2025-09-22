from __future__ import annotations

import asyncio

import zendriver
from loguru import logger

from xilriws.constants import ACCESS_URL
from xilriws.extension_comm import FINISH_COOKIE_PURGE, ExtensionComm, FINISH_PROXY
from xilriws.proxy import ProxyDistributor
from xilriws.ptc import ptc_utils
from xilriws.ptc_auth import LoginException
from xilriws.reese_cookie import ReeseCookie

from .browser import Browser, ProxyException

logger = logger.bind(name="Browser")


class BrowserAuth(Browser):
    def __init__(self, extension_paths: list[str], proxies: ProxyDistributor, ext_comm: ExtensionComm):
        super().__init__(extension_paths=extension_paths, ext_comm=ext_comm)
        self.proxies = proxies

    async def get_reese_cookie(self, proxy_changed: bool) -> ReeseCookie | None:
        proxy = self.proxies.next_proxy

        try:
            await self.start_browser()
        except Exception as e:
            logger.exception("Exception while starting browser", e)
            return None

        try:
            js_future, js_check_handler = await self.get_js_check_handler(ACCESS_URL)
            cookie_future = await self.ext_comm.add_listener(FINISH_COOKIE_PURGE)

            await self.new_tab()
            if proxy_changed:
                await self.change_proxy()

            if not self.first_run and cookie_future and not cookie_future.done():
                try:
                    await asyncio.wait_for(cookie_future, 2)
                except asyncio.TimeoutError:
                    logger.info("Didn't get confirmation that cookies were cleared, continuing anyway")

            self.first_run = False

            if self.last_cookies:
                await self.browser.cookies.set_all(self.last_cookies)

            # if IS_DEBUG:
            #     await self.log_ip()

            self.tab.add_handler(zendriver.cdp.network.ResponseReceived, js_check_handler)
            logger.info("Opening PTC")

            try:
                await asyncio.wait_for(self.tab.get(url=ACCESS_URL + "login"), timeout=20)
                html = await asyncio.wait_for(self.tab.get_content(), timeout=20)
            except asyncio.TimeoutError:
                raise ProxyException(f"Page timed out (Proxy: {proxy.url})")

            if "neterror" in html.lower():
                raise ProxyException(f"Page couldn't be reached (Proxy: {proxy.url})")

            imp_code, imp_reason = ptc_utils.get_imperva_error_code(html)
            if imp_code not in ("15", "?"):
                proxy.rate_limited()
                raise LoginException(f"Error code {imp_code} ({imp_reason}) with (Proxy: {proxy.url})")
            else:
                logger.info("Successfully got error 15 page")
                if not js_future.done():
                    try:
                        logger.info("Waiting for JS check")
                        await asyncio.wait_for(js_future, timeout=100)
                        self.tab.handlers.clear()
                        logger.info("JS check done. reloading")
                    except asyncio.TimeoutError:
                        raise LoginException("Timeout on JS challenge")
                else:
                    logger.debug("JS check already done, continuing")

                logger.debug("Reloading now")
                await self.tab.reload()

                attempts = 0
                finished_reloading = False
                while attempts < 10 and not finished_reloading:
                    # This while loop checks the html until it finds "log in" or an imperva error code.
                    # Before adding it, it would often log an error code "?". These seem to have been imperva
                    # error pages that weren't loaded properly. But to make absolutely sure, we'll just retry.
                    attempts += 1
                    logger.debug(f"Checking reload content #{attempts}")

                    new_html = await self.tab.get_content()
                    if "log in" not in new_html.lower():
                        logger.debug(new_html)
                        proxy.rate_limited()
                        imp_code, imp_reason = ptc_utils.get_imperva_error_code(new_html)
                        if imp_code != "?":
                            raise LoginException(f"Didn't pass JS check. Code {imp_code} ({imp_reason})")

                        await self.tab.sleep(0.5)
                    else:
                        logger.info("Finished reloading")
                        finished_reloading = True

                if not finished_reloading:
                    raise LoginException("Timed out while waiting for reload to finish")

            logger.info("Getting cookies from browser")
            all_cookies = await self.get_cookies()

            self.consecutive_failures = 0
            return ReeseCookie(all_cookies, proxy)
        except LoginException as e:
            logger.error(f"{str(e)} while getting cookie")
            self.consecutive_failures += 1
            return None
        except ProxyException as e:
            # proxy.invalidate()
            proxy.rate_limited()
            logger.error(f"{str(e)} while getting cookie")
            await self.stop_browser()
            return None
        except Exception as e:
            logger.exception("Exception in browser", e)

        logger.error(
            "Error while getting cookie from browser, it will be restarted next time"
        )
        self.consecutive_failures += 1
        await self.stop_browser()
        return None

    async def change_proxy(self):
        proxy_future = await self.ext_comm.add_listener(FINISH_PROXY)
        # TODO: add try/except and restart the browser
        used_proxy = await self.proxies.change_proxy()

        if used_proxy:
            try:
                await asyncio.wait_for(proxy_future, 2)
            except asyncio.TimeoutError:
                logger.info("Didn't get confirmation that proxy changed, continuing anyway")
