from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum

from litestar import Litestar, Request, Response, post
from litestar.di import Provide
from litestar.status_codes import (
    HTTP_200_OK,
    HTTP_400_BAD_REQUEST,
    HTTP_418_IM_A_TEAPOT,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_408_REQUEST_TIMEOUT,
)
from loguru import logger

from xilriws.browser import Browser
from xilriws.constants import AUTH_TIMEOUT
from xilriws.proxy import ProxyDistributor
from xilriws.proxy_dispenser import ProxyDispenser
from xilriws.ptc_auth import InvalidCredentials, LoginException, PtcAuth, PtcBanned
from xilriws.reese_cookie import CookieMonster

from .basic_mode import BasicMode

logger = logger.bind(name="Xilriws")


@dataclass
class AuthRequest:
    username: str
    password: str
    url: str


class AuthResponseStatus(Enum):
    SUCCESS = 1
    ERROR = 2
    INVALID = 3
    BANNED = 4
    TIMEOUT = 5


@dataclass
class AuthResponse:
    status: str
    login_code: str = ""


@post("/api/v1/login-code")
async def auth_endpoint(request: Request, ptc_auth: PtcAuth, data: AuthRequest) -> Response[AuthResponse]:
    try:
        login_code = await asyncio.wait_for(ptc_auth.auth(data.username, data.password, data.url), timeout=AUTH_TIMEOUT)

        logger.success("200 OK: successful auth")
        return Response(
            AuthResponse(login_code=login_code, status=AuthResponseStatus.SUCCESS.name), status_code=HTTP_200_OK
        )
    except InvalidCredentials:
        logger.warning("400 Bad Request: Invalid credentials")
        return Response(AuthResponse(status=AuthResponseStatus.INVALID.name), status_code=HTTP_400_BAD_REQUEST)
    except PtcBanned:
        logger.warning("418: account is ptc-banned")
        return Response(AuthResponse(status=AuthResponseStatus.BANNED.name), status_code=HTTP_418_IM_A_TEAPOT)
    except LoginException as e:
        logger.error(f"Error: {str(e)}")
    except asyncio.TimeoutError:
        logger.error("408: Exceeded timeout")
        return Response(
            AuthResponse(status=AuthResponseStatus.TIMEOUT.name),
            status_code=HTTP_408_REQUEST_TIMEOUT,
        )
    except Exception as e:
        logger.exception(e)

    logger.warning("500 Internal Server Error: Additional output above")
    return Response(AuthResponse(status=AuthResponseStatus.ERROR.name), status_code=HTTP_500_INTERNAL_SERVER_ERROR)


@dataclass
class ActivateRequest:
    email: str
    code: str


class ActivateResponseStatus(Enum):
    SUCCESS = 1
    NO_OPEN_ACTIVATION = 2


@dataclass
class ActivateResponse:
    status: str
    username: str | None = None
    email: str | None = None
    password: str | None = None


@post("/api/v1/activate")
async def activate_endpoint(data: ActivateRequest) -> ActivateResponse:
    return ActivateResponse(status=ActivateResponseStatus.NO_OPEN_ACTIVATION.name)


class AuthMode(BasicMode):
    def __init__(self, browser: Browser, proxies: ProxyDistributor, proxy_dispenser: ProxyDispenser):
        self.cookie_monster = CookieMonster(browser, proxies, proxy_dispenser)
        self.ptc_auth = PtcAuth(self.cookie_monster)

    async def prepare(self) -> None:
        await self.cookie_monster.prepare()

    async def _get_ptc_auth(self):
        return self.ptc_auth

    def get_litestar(self) -> Litestar:
        return Litestar(
            route_handlers=[auth_endpoint, activate_endpoint],
            dependencies={"ptc_auth": Provide(self._get_ptc_auth)}
        )
