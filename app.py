from __future__ import annotations

import asyncio
import json
import logging
import os.path
import signal
import sys

import uvicorn
from loguru import logger

from xilriws.mode import CionMode, AuthMode
from xilriws.browser import Browser

httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.CRITICAL)
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.setLevel(logging.CRITICAL)
nodriver_logger = logging.getLogger("nodriver")
nodriver_logger.setLevel(logging.CRITICAL)

logger = logger.bind(name="Xilriws")

CION_MODE = True


async def main():
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config: dict[str, str | int] = json.load(f)
    else:
        config = {}

    browser = Browser(
        [
            config.get("fingerprint_random_path", "/xilriws/xilriws-fingerprint-random/"),
            config.get("cookie_delete_path", "/xilriws/xilriws-cookie-delete/"),
        ]
    )

    if CION_MODE:
        mode = CionMode(browser)
    else:
        mode = AuthMode(browser)

    await mode.prepare()

    port = config.get("port", 5090)
    host = config.get("host", "0.0.0.0")

    app = mode.get_litestar()
    server_config = uvicorn.Config(app, port=port, host=host, log_config=None)
    server = uvicorn.Server(server_config)

    if sys.platform != "win32":
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    logger.info(f"Starting Xilriws on http://{host}:{port}")

    await server.serve()


asyncio.run(main())
