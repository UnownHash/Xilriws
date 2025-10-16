from __future__ import annotations

import asyncio
import json
from typing import Any, Literal

import websockets
from loguru import logger
from xilriws.proxy import Proxy

logger = logger.bind(name="ExtComm")

FINISH_PROXY = "finish:setProxy"
FINISH_COOKIE_PURGE = "finish:cookiePurge"


class ExtensionComm:
    def __init__(self):
        self.clients: set[websockets.WebSocketServerProtocol] = set()
        self.futures: dict[str, list[asyncio.Future]] = {}

    async def send(self, action: str, data: dict[str, Any] | None = None):
        message = json.dumps(
            {
                "action": action,
                "data": data
            }
        )
        logger.debug(f"Sending WS data: {message}")
        for client in self.clients:
            await client.send(message)

    async def set_proxy(self, proxy: Proxy):
        await self.send(
            "setProxy",
            {
                "host": proxy.host,
                "port": proxy.port,
                "scheme": proxy.scheme if proxy.scheme else None,
                "password": proxy.password,
                "username": proxy.username,
            },
        )

    # async def fetch(self, url: str, headers: dict[str, str], method: str, referrer: str, body: str):

    async def echo(self, websocket: websockets.WebSocketServerProtocol):
        self.clients.add(websocket)
        try:
            async for message in websocket:
                logger.debug(f"Received WS data: {message}")
                data = json.loads(message)
                action = data["action"]
                detail = data["detail"]

                futures = self.futures.get(action)
                if not futures:
                    continue

                for future in futures:
                    try:
                        future.set_result(detail)
                    except asyncio.InvalidStateError:
                        continue
                del self.futures[action]

            await websocket.wait_closed()
        except websockets.exceptions.ConnectionClosedError:
            self.clients.remove(websocket)
        except Exception as e:
            logger.exception("Error in WS server", e)
        finally:
            self.clients.remove(websocket)

    async def add_listener(self, action: str) -> asyncio.Future:
        future = asyncio.get_running_loop().create_future()
        if action in self.futures:
            self.futures[action].append(future)
        else:
            self.futures[action] = [future]
        return future

    async def start(self):
        async with websockets.serve(self.echo, "127.0.0.1", 9091):
            await asyncio.Future()
