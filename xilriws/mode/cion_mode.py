from __future__ import annotations

import litestar.logging
from litestar import Litestar, post
from litestar.di import Provide
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_503_SERVICE_UNAVAILABLE
from loguru import logger
from dataclasses import dataclass

from xilriws.browser import Browser, CionResponse
from xilriws.ptc_join import PtcJoin
from .basic_mode import BasicMode
from xilriws.proxy import ProxyDistributor, Proxy
from xilriws.proxy_dispenser import ProxyDispenser

logger = logger.bind(name="Xilriws")


@dataclass
class CionRequest:
    proxy: str | None


@post("/api/v1/cion")
async def cion_endpoint(ptc_join: PtcJoin, data: CionRequest) -> list[CionResponse]:
    if ptc_join.is_running:
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE)

    try:
        tokens = await ptc_join.get_join_tokens(data.proxy)
        if tokens:
            logger.success("200: Returned tokens to Cion")
            return [tokens]

        return []

    except Exception as e:
        logger.exception(e)
    logger.error("500: Internal Xilriws error, look above")
    raise HTTPException("internal error")


class CionMode(BasicMode):
    def __init__(self, browser: Browser, proxies: ProxyDistributor, proxy_dispenser: ProxyDispenser):
        self.ptc_join = PtcJoin(browser, proxies, proxy_dispenser)
        self.current_proxy_index = 0

    async def prepare(self) -> None:
        # await self.ptc_join.prepare()
        pass

    async def _get_ptc_join(self):
        return self.ptc_join

    def get_litestar(self) -> Litestar:
        return Litestar(
            route_handlers=[cion_endpoint],
            dependencies={"ptc_join": Provide(self._get_ptc_join)},
        )
