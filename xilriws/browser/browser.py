from __future__ import annotations

import asyncio
import os
import re
import sys
from typing import Callable

import nodriver
from loguru import logger

from xilriws.debug import IS_DEBUG
from xilriws.extension_comm import ExtensionComm
from xilriws.extension_comm import FINISH_PROXY
from xilriws.proxy import ProxyDistributor
from xilriws.ptc_auth import LoginException
from xilriws.ptc.ptc_utils import USER_AGENT

logger = logger.bind(name="Browser")
HEADLESS = not IS_DEBUG


class ProxyException(Exception):
    pass


class Browser:
    browser: nodriver.Browser | None = None
    tab: nodriver.Tab | None = None
    consecutive_failures = 0
    last_cookies: list[nodriver.cdp.network.CookieParam] | None = None
    session_count = 0
    first_run = True

    def __init__(self, extension_paths: list[str], proxies: ProxyDistributor, ext_comm: ExtensionComm):
        self.extension_paths: list[str] = extension_paths
        self.proxies = proxies
        self.ext_comm = ext_comm

    async def start_browser(self):
        if self.consecutive_failures >= 30:
            logger.critical(f"{self.consecutive_failures} consecutive failures in the browser! this is really bad")
            await asyncio.sleep(60 * 30)
            self.consecutive_failures -= 1
            return None

        logger.info("Browser starting")

        if self.browser:
            self.session_count += 1

            if self.session_count % 60 == 0:
                logger.info("Time for a browser restart")
                await self.stop_browser()
            elif not await self.health_check():
                logger.info("Browser seems stale. Restarting")
                await self.stop_browser()

        if not self.browser:
            config = nodriver.Config(headless=HEADLESS, browser_executable_path=self.__find_chrome_executable())
            config.add_argument(f"--user-agent={USER_AGENT}")
            if not IS_DEBUG:
                config.add_argument("--window-size=1,1")

            disabled_features = [
                "OptimizationHints",
                "OptimizationHintsFetching",
                "OptimizationHintsFetchingAnonymousDataConsent",
                "ContextMenuPerformanceInfoAndRemoteHintFetching",
                "OptimizationTargetPrediction",
                "OptimizationGuideModelDownloading",
                "OptimizationGuidePageContentExtraction",
                "OptimizationHintsComponent",
                "OptimizationHintsFetchingSRP",
                "OptimizationPersonalizedHintsFetching",
                "OptimizationGuideModelExecution",
                "Translate",
                "BackForwardCache",
                "AcceptCHFrame",
                "MediaRouter",
                "DialMediaRouteProvider"
            ]
            config.add_argument(f"--disable-features={','.join(disabled_features)}")
            config.add_argument("--disable-hang-monitor")
            config.add_argument("--disable-background-networking")
            config.add_argument("--disable-breakpad")
            config.add_argument("--disable-default-apps")
            config.add_argument("--disable-renderer-backgrounding")
            config.add_argument("--no-first-run")


            try:
                for path in self.extension_paths:
                    config.add_extension(path)

                self.browser = await nodriver.start(config)
                full_command = f"{config.browser_executable_path} {' '.join(config())}"
                logger.info(f"Starting browser: `{full_command}`")

                if "brave" in self.browser.config.browser_executable_path.lower():
                    self.tab = await self.browser.get("brave://settings/shields")
                    await self.__set_setting(
                        shadow_roots=[
                            "settings-ui",
                            "settings-main",
                            "settings-basic-page",
                            "settings-default-brave-shields-page",
                        ],
                        element_id="fingerprintingSelectControlType",
                        new_value="allow",
                        tab=self.tab,
                    )

                    await self.tab.get("brave://settings/privacy")
                    await self.__set_setting(
                        shadow_roots=[
                            "settings-ui",
                            "settings-main",
                            "settings-basic-page",
                            "settings-privacy-page",
                            "settings-brave-personalization-options",
                            "settings-dropdown-menu",
                        ],
                        element_id="dropdownMenu",
                        new_value="disable_non_proxied_udp",
                        tab=self.tab,
                    )
            except Exception as e:
                full_command = f"{config.browser_executable_path} {' '.join(config())}"
                logger.error(str(e))
                logger.error(
                    f"Error while starting the browser. Please confirm you can start it manually by running "
                    f"`{full_command}`"
                )
                raise e

    async def __set_setting(self, shadow_roots: list[str], element_id: str, new_value: str, tab: nodriver.Tab):
        await tab.wait_for(shadow_roots[0])

        inject_js = "const element=document."
        inject_js += ".".join(f"querySelector('{s}').shadowRoot" for s in shadow_roots)
        inject_js += f".getElementById('{element_id}');"
        inject_js += f"element.value='{new_value}';"
        inject_js += "element.dispatchEvent(new Event('change'));"

        try:
            await tab.evaluate(inject_js)
        except Exception as e:
            logger.warning(f"{str(e)} while changing setting {element_id}, ignoring")

    async def health_check(self) -> bool:
        async def _check():
            if not self.tab:
                self.tab = await self.browser.get("about:blank")
            resp = await self.tab.send(nodriver.cdp.browser.get_version())
            try:
                logger.debug(f"Health Check - Chrome version is {resp[1]}")
            except IndexError:
                pass

        try:
            await asyncio.wait_for(_check(), timeout=10)
            return True
        except Exception:
            return False

    async def get_cookies(self) -> dict[str, str]:
        reese_value: str | None = None
        attempts = 10
        while not reese_value and attempts > 0:
            attempts -= 1

            cookies = await self.tab.send(nodriver.cdp.network.get_cookies())
            for cookie in cookies:
                if cookie.name == "reese84":
                    logger.info("Got cookies")
                    reese_value = cookie.value
                    continue

            if not reese_value:
                await self.tab.wait(0.3)
            else:
                self.last_cookies = cookies

        if not reese_value:
            raise LoginException("Didn't find reese cookie in browser")

        return {c.name: c.value for c in self.last_cookies}

    async def get_js_check_handler(self, url: str) -> tuple[asyncio.Future, Callable]:
        js_future = asyncio.get_running_loop().create_future()
        basic_url = url.replace("https://", "").replace("/", "")

        async def js_check_handler(event: nodriver.cdp.network.ResponseReceived):
            handler_url = event.response.url
            if not handler_url.startswith(url):
                return
            if not handler_url.endswith(f"?d={basic_url}"):
                return
            if not js_future.done():
                logger.debug(f"Passed JS check ({handler_url})")
                js_future.set_result(True)

        return js_future, js_check_handler

    async def change_proxy(self):
        proxy_future = await self.ext_comm.add_listener(FINISH_PROXY)
        # TODO: add try/except and restart the browser
        used_proxy = await self.proxies.change_proxy()

        if used_proxy:
            try:
                await asyncio.wait_for(proxy_future, 2)
            except asyncio.TimeoutError:
                logger.info("Didn't get confirmation that proxy changed, continuing anyway")

    async def new_tab(self):
        logger.info("Opening tab")
        if not self.tab:
            self.tab = await self.browser.get("about:blank")
        else:
            tab = await self.tab.get("about:blank", new_tab=True)
            await self.tab.close()
            self.tab = tab
        await self.tab.sleep(0.4)

    async def new_private_window(self):
        context_id = await self.browser.connection.send(nodriver.cdp.target.create_browser_context())
        target_id = await self.browser.connection.send(
            nodriver.cdp.target.create_target("about:blank", browser_context_id=context_id)
        )
        if self.tab:
            await self.tab.close()
        self.tab = next(
            filter(
                lambda item: item.type_ == "page" and item.target_id == target_id,
                self.browser.targets,
            )
        )

    async def __enable_private_extension(self, tab: nodriver.Tab):
        await tab.get("brave://extensions/")
        await tab.wait_for("extensions-manager")
        await tab.evaluate(
            "document.querySelector('extensions-manager').shadowRoot"
            ".querySelector('extensions-item-list').shadowRoot"
            ".querySelector('extensions-item').shadowRoot"
            ".querySelector('cr-button')"
            ".click()"
        )
        await tab.wait_for("extensions-manager")

        await tab.evaluate(
            "document.querySelector('extensions-manager').shadowRoot"
            ".querySelector('#viewManager > extensions-detail-view.active').shadowRoot"
            ".querySelector('#allow-incognito').shadowRoot"
            ".querySelector('label#label input')"
            ".click()"
        )

    async def log_ip(self):
        await self.tab.get(url="https://api.ipify.org/")
        ip_html = await self.tab.get_content()
        ip = re.search(r"\d*\.\d*\.\d*\.\d*", ip_html)
        if ip and ip.group(0):
            logger.info(f"Browser IP check: {ip.group(0)}")
        else:
            logger.info("Browser IP check failed")

    async def log_canvas_fingerprint(self):
        await self.tab.get("https://browserleaks.com/canvas")
        await self.tab.wait_for("#canvas-hash")
        c = await self.tab.get_content()
        for line in c.split("\n"):
            if 'id="canvas-hash"' in line:
                logger.info(f"Canvas fingerprint: {line}")

    async def stop_browser(self):
        self.browser.stop()
        self.first_run = True
        self.tab = None
        self.browser = None

    def __find_chrome_executable(self, return_all=False):
        candidates = []
        if sys.platform.startswith(("darwin", "cygwin", "linux", "linux2")):
            for item in os.environ.get("PATH").split(os.pathsep):
                for subitem in (
                    "brave",
                    "brave-browser",
                    "google-chrome",
                    "chromium",
                    "chromium-browser",
                    "chrome",
                    "google-chrome-stable",
                ):
                    candidates.append(os.sep.join((item, subitem)))
            if "darwin" in sys.platform:
                candidates += [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "/Applications/Chromium.app/Contents/MacOS/Chromium",
                ]

        else:
            for item in map(
                os.environ.get,
                ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA", "PROGRAMW6432"),
            ):
                if item is not None:
                    for subitem in (
                        # "BraveSoftware/Brave-Browser/Application",
                        # "Google/Chrome/Application",
                        # "Google/Chrome Beta/Application",
                        # "Google/Chrome Canary/Application",
                        "Chromium/Application"
                    ):
                        # candidates.append(os.sep.join((item, subitem, "brave.exe")))
                        candidates.append(os.sep.join((item, subitem, "chrome.exe")))
        rv = []
        for candidate in candidates:
            if os.path.exists(candidate) and os.access(candidate, os.X_OK):
                logger.debug("%s is a valid candidate... " % candidate)
                rv.append(candidate)

        winner = None

        if return_all and rv:
            return rv

        winner = next((r for r in rv if "brave" in r.lower()), None)

        if not winner:
            if rv and len(rv) > 1:
                # assuming the shortest path wins
                winner = min(rv, key=lambda x: len(x))

            elif len(rv) == 1:
                winner = rv[0]

        if winner:
            return os.path.normpath(winner)

        raise FileNotFoundError(
            "could not find a valid chrome browser binary. please make sure chrome is installed."
            "or use the keyword argument 'browser_executable_path=/path/to/your/browser' "
        )
