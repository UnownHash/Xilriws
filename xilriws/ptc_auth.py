from __future__ import annotations

import re
from typing import TYPE_CHECKING

import httpx
from loguru import logger
from curl_cffi import requests

from .config import config
from .constants import ACCESS_URL
from xilriws.ptc import ptc_utils

if TYPE_CHECKING:
    from .reese_cookie import CookieMonster, ReeseCookie

logger = logger.bind(name="PTC")


class LoginException(Exception):
    """generic login exception, don't log the traceback"""

    pass


class InvalidCredentials(LoginException):
    """Invalid account credentials"""

    pass


class PtcBanned(Exception):
    """account is ptc banned, report as such"""
    pass


class PtcAuth:
    def __init__(self, cookie_monster: CookieMonster):
        self.cookie_monster = cookie_monster

    async def auth(self, username: str, password: str, full_url: str) -> str:
        logger.info(f"Starting auth for {username}")

        # proxies = None
        # if proxy:
        #     proxies = {"http://": proxy, "https://": proxy}

        attempts = config.auth.max_auth_attempts
        while attempts > 0:
            attempts -= 1
            cookie = await self.cookie_monster.get_reese_cookie()

            async with requests.AsyncSession(
                headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-us",
                    "Connection": "keep-alive",
                    "Accept-Encoding": "gzip, deflate, br",
                    "User-Agent": ptc_utils.USER_AGENT,
                },
                allow_redirects=True,
                verify=False,
                timeout=10,
                proxy=cookie.proxy.full_url.geturl(),
                cookies=cookie.cookies,
                impersonate="chrome146",
            ) as client:
                logger.info("Calling OAUTH page")

                try:
                    resp = await client.get(full_url)
                except Exception as e:
                    logger.error(f"Error {str(e)} during OAUTH")
                    continue

                if not await self.__check_status(resp, cookie):
                    continue

                csrf, challenge = self.__extract_csrf_and_challenge(resp.text)

                logger.info("Calling LOGIN page")

                try:
                    login_resp = await client.post(
                        ACCESS_URL + "login",
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        data={"_csrf": csrf, "challenge": challenge, "email": username, "password": password},
                    )
                except Exception as e:
                    logger.error(f"Error {str(e)} during LOGIN")
                    continue

                if not await self.__check_status(login_resp, cookie):
                    continue

                login_code = self.__extract_login_code(login_resp.text)

                if not login_code:
                    if "error-message" in login_resp.text:
                        self.check_error_on_login_page(login_resp.text)
                        logger.error(
                            f"Please send this to Malte on Discord (error page after login)\n{login_resp.text}"
                        )
                        raise LoginException("Login failed, probably invalid credentials")

                    logger.info("Calling CONSENT page")

                    try:
                        logger.debug(login_resp.text)
                        csrf_consent, challenge_consent = self.__extract_csrf_and_challenge(login_resp.text)
                    except LoginException:
                        logger.error(f"Could not find a CSRF token for account {username} - it's probably unactivated")
                        raise InvalidCredentials()

                    try:
                        resp_consent = await client.post(
                            ACCESS_URL + "consent",
                            data={"challenge": challenge_consent, "_csrf": csrf_consent, "allow_submit": "Allow"},
                        )
                    except Exception as e:
                        logger.error(f"Error {str(e)} during CONSENT")
                        continue

                    if not await self.__check_status(resp_consent, cookie):
                        continue

                    login_code = self.__extract_login_code(resp_consent.text)
                    if not login_code:
                        raise LoginException("No Login Code after consent, please check account")
                return login_code

        raise LoginException("Exceeded max retries during PTC auth")

    async def __check_status(self, resp: httpx.Response, cookie: ReeseCookie) -> bool:
        if resp.status_code == 403 or "Request unsuccessful. Incapsula" in resp.text:
            await self.handle_imperva_error(resp.text, cookie)
            return False

        logger.debug(f"PTC response: {resp.status_code} | {resp.text}")

        if resp.status_code == 418:
            raise PtcBanned()

        if resp.status_code != 200:
            raise LoginException(f"PTC: {resp.status_code} but expected 200 - {resp.text}")

        return True

    async def handle_imperva_error(self, html: str, cookie: ReeseCookie):
        imp_code, imp_reason = ptc_utils.get_imperva_error_code(html)
        await self.cookie_monster.remove_cookie(cookie)
        cookie.proxy.rate_limited()
        logger.warning(
            f"Error code {imp_code} ({imp_reason}) during PTC request, trying again with another proxy (Proxy: {cookie.proxy.url})"
        )

    def check_error_on_login_page(self, content: str):
        if "Your username or password is incorrect." in content:
            logger.warning("BROWSER: Incorrect credentials")
            raise InvalidCredentials("Incorrect account credentials")
        elif "your account has been disabled for" in content:
            logger.error("BROWSER: Account is temporarily disabled")
            raise InvalidCredentials("Account temporarily disabled")
        elif "We are unable to log you in to this account. Please contact Customer Service for additional details." in content:
            raise PtcBanned()

    def __extract_login_code(self, html) -> str | None:
        matches = re.search(r"pokemongo://state=(.*?)(?:,code=(.*?))?(?='|$)", html)

        if matches and len(matches.groups()) == 2:
            return matches.group(2)

    def __extract_csrf_and_challenge(self, html: str) -> tuple[str, str]:
        csrf_regex = re.compile(r'name="_csrf" value="(.*?)">')
        challenge_regex = re.compile(r'name="challenge" value="(.*?)">')

        csrf_matches = csrf_regex.search(html)
        challenge_matches = challenge_regex.search(html)

        if csrf_matches and challenge_matches:
            return csrf_matches.group(1), challenge_matches.group(1)

        raise LoginException("Couldn't find CSRF or challenge in Auth response")
