from __future__ import annotations

import asyncio
import os
import re
import sys
from typing import Callable
import typing

import zendriver
from loguru import logger

from xilriws.debug import IS_DEBUG
from xilriws.extension_comm import ExtensionComm
from xilriws.proxy import ProxyDistributor
from xilriws.ptc_auth import LoginException
from xilriws.ptc.ptc_utils import USER_AGENT

logger = logger.bind(name="Browser")
HEADLESS = not IS_DEBUG


class ProxyException(Exception):
    pass


class Browser:
    browser: zendriver.Browser | None = None
    tab: zendriver.Tab | None = None
    consecutive_failures = 0
    last_cookies: list[zendriver.cdp.network.CookieParam] | None = None
    session_count = 0
    first_run = True

    def __init__(self, extension_paths: list[str], ext_comm: ExtensionComm):
        self.extension_paths: list[str] = extension_paths
        self.ext_comm = ext_comm

    async def start_browser(self):
        if self.consecutive_failures >= 30:
            logger.critical(f"{self.consecutive_failures} consecutive failures in the browser! this is really bad")
            # await asyncio.sleep(60 * 30)
            self.consecutive_failures -= 1

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
            config = zendriver.Config(headless=HEADLESS, browser_executable_path=self.__find_chrome_executable())
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
                "DialMediaRouteProvider",
                "IsolateOrigins",
                "DisableLoadExtensionCommandLineSwitch"
            ]
            config.add_argument(f"--disable-features={','.join(disabled_features)}")
            config.add_argument("--disable-hang-monitor")
            config.add_argument("--disable-background-networking")
            config.add_argument("--disable-breakpad")
            config.add_argument("--disable-default-apps")
            config.add_argument("--disable-renderer-backgrounding")
            config.add_argument("--no-first-run")
            config.add_argument("--disable-web-security")


            try:
                for path in self.extension_paths:
                    config.add_extension(path)

                self.browser = await zendriver.start(config)
                full_command = f"{self.browser.config.browser_executable_path} {' '.join(self.browser.config())}"
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

    async def __set_setting(self, shadow_roots: list[str], element_id: str, new_value: str, tab: zendriver.Tab):
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
            resp = await self.tab.send(zendriver.cdp.browser.get_version())
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

            cookies = await self.tab.send(zendriver.cdp.network.get_cookies())
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

        async def js_check_handler(event: zendriver.cdp.network.ResponseReceived):
            handler_url = event.response.url
            if not handler_url.startswith(url):
                return
            if not handler_url.endswith(f"?d={basic_url}"):
                return
            if not js_future.done():
                logger.debug(f"Passed JS check ({handler_url})")
                js_future.set_result(True)

        return js_future, js_check_handler

    async def new_tab_timeout(self):
        await asyncio.wait_for(self.new_tab(), 10)

    async def _register_handlers(self) -> None:
        """
        this is a copy of zendriver.connection.Connection._register_handlers
        to monkey-patch a race condition when opening tabs

        ensure that for current (event) handlers, the corresponding
        domain is enabled in the protocol.

        """
        # save a copy of current enabled domains in a variable
        # domains will be removed from this variable
        # if it is still needed according to the set handlers
        # so at the end this variable will hold the domains that
        # are not represented by handlers, and can be removed
        enabled_domains = self.tab.enabled_domains.copy()
        for event_type in self.tab.handlers.copy():
            logger.info(1)
            if len(self.tab.handlers[event_type]) == 0:
                self.tab.handlers.pop(event_type)
                continue
            if not isinstance(event_type, type):
                continue
            domain_mod = zendriver.util.cdp_get_module(event_type.__module__)
            if domain_mod in self.tab.enabled_domains:
                # at this point, the domain is being used by a handler
                # so remove that domain from temp variable 'enabled_domains' if present
                if domain_mod in enabled_domains:
                    enabled_domains.remove(domain_mod)
                continue
            elif domain_mod not in self.tab.enabled_domains:
                if domain_mod in (zendriver.cdp.target, zendriver.cdp.storage):
                    # by default enabled
                    continue
                try:
                    # we add this before sending the request, because it will
                    # loop indefinite
                    logger.debug("registered %s", domain_mod)
                    self.tab.enabled_domains.append(domain_mod)

                    await self.send(domain_mod.enable(), _is_update=True)

                except:  # noqa - as broad as possible, we don't want an error before the "actual" request is sent
                    logger.debug("", exc_info=True)
                    try:
                        self.tab.enabled_domains.remove(domain_mod)
                    except:  # noqa
                        logger.debug("NOT GOOD", exc_info=True)
                        continue
                finally:
                    continue
        for ed in enabled_domains:
            # we started with a copy of self.tab.enabled_domains and removed a domain from this
            # temp variable when we registered it or saw handlers for it.
            # items still present at this point are unused and need removal
            self.tab.enabled_domains.remove(ed)

    async def aopen(self) -> None:
        """
        this is a copy of zendriver.connection.Connection.aopen
        to monkey-patch a race condition when opening tabs

        opens the websocket connection. should not be called manually by users
        :param kw:
        :return:
        """
        import websockets

        if self.tab.websocket is None:
            try:
                self.tab.websocket = await websockets.connect(
                    self.tab.websocket_url,
                    ping_timeout=900,
                    max_size=2**28,
                )
                logger.info(2)
                self.tab.listener = zendriver.core.connection.Listener(self.tab)
            except (Exception,) as e:
                logger.debug("exception during opening of websocket : %s", e)
                if self.tab.listener:
                    self.tab.listener.cancel()
                raise
        if not self.tab.listener or not self.tab.listener.running:
            logger.info(3)
            self.tab.listener = zendriver.core.connection.Listener(self.tab)
            logger.debug("opened websocket connection to %s", self.tab.websocket_url)

        # when a websocket connection is closed (either by error or on purpose)
        # and reconnected, the registered event listeners (if any), should be
        # registered again, so the browser sends those events
        await self._register_handlers()

    async def send(
        self,
        cdp_obj: typing.Generator[dict[str, typing.Any], dict[str, typing.Any], typing.T],
        _is_update: bool = False,
    ) -> typing.T:
        """
        this is a copy of zendriver.connection.Connection.send
        to monkey-patch a race condition when opening tabs

        send a protocol command. the commands are made using any of the cdp.<domain>.<method>()'s
        and is used to send custom cdp commands as well.

        :param cdp_obj: the generator object created by a cdp method

        :param _is_update: internal flag
            prevents infinite loop by skipping the registeration of handlers
            when multiple calls to connection.send() are made
        :return:
        """
        import itertools
        logger.info("send")

        logger.info(1)
        if not _is_update:
            await self.aopen()
        logger.info(2)
        if self.tab.websocket is None:
            return  # type: ignore
        if self.tab._owner:
            logger.info(3)
            browser = self.tab._owner
            # if browser.config:
            #     if browser.config.expert:
            #         await self.tab._prepare_expert()
            #     if browser.config.headless:
            #         await self.tab._prepare_headless()
        if (
            not self.tab.listener
            or not self.tab.listener.running
        ):
            self.tab.listener = zendriver.core.connection.Listener(
                self.tab
            )

        tx = zendriver.core.connection.Transaction(cdp_obj)
        tx.connection = self.tab
        if not self.tab.mapper:
            logger.info(6)
            self.tab.__count__ = itertools.count(0)
        async with self.tab._current_id_mutex:
            logger.info(7)
            tx.id = next(self.tab.__count__)
        self.tab.mapper.update({tx.id: tx})
        if not _is_update:
            logger.info(9)
            await self.tab._register_handlers()
        await self.tab.websocket.send(tx.message)
        try:
            if not tx.method == "Network.enable":
                return await tx  # type: ignore
        except Exception as e:
            e.message = e.message or ""
            e.message += f"\ncommand:{tx.method}\nparams:{tx.params}"
            raise e

    async def new_tab(self):
        logger.info("Opening tab")

        if not self.tab:
            self.tab = await self.browser.get("about:blank")
        else:
            tab = await self.tab.get("about:blank", new_tab=True)
            await self.tab.close()
            self.tab = tab

    async def get_page(self, url: str):
        future = asyncio.get_running_loop().create_future()
        event_type = zendriver.cdp.target.TargetInfoChanged

        async def get_handler(event: zendriver.cdp.target.TargetInfoChanged) -> None:
            if future.done():
                return

            if event.target_info.url == url:
                future.set_result(event)

        self.tab.browser.connection.add_handler(event_type, get_handler)

        await self.send(zendriver.cdp.page.navigate(url))

        try:
            await asyncio.wait_for(future, 10)
        except:
            raise LoginException("Timeout while opening tab. this is probably a bug")
        self.tab.browser.connection.remove_handlers(event_type, get_handler)

    async def new_private_window(self):
        context_id = await self.browser.connection.send(zendriver.cdp.target.create_browser_context())
        target_id = await self.browser.connection.send(
            zendriver.cdp.target.create_target("about:blank", browser_context_id=context_id)
        )
        if self.tab:
            await self.tab.close()
        self.tab = next(
            filter(
                lambda item: item.type_ == "page" and item.target_id == target_id,
                self.browser.targets,
            )
        )

    async def __enable_private_extension(self, tab: zendriver.Tab):
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
        await self.browser.stop()
        self.first_run = True
        self.tab = None
        self.browser = None

    def __find_chrome_executable(self, return_all=False):
        candidates = ["/xilriws/chromium/chrome", "/chromium/chrome"]
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
                        "Chromium/Application",
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
