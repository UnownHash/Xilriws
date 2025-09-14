from __future__ import annotations

import asyncio
import json
import logging
import os.path
import signal
import sys

import uvicorn
from loguru import logger

from xilriws.browser import BrowserAuth, BrowserJoin
from xilriws.extension_comm import ExtensionComm
from xilriws.mode import AuthMode, CionMode
from xilriws.proxy import ProxyDistributor
from xilriws.proxy_dispenser import ProxyDispenser
from xilriws.task_creator import task_creator

httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.CRITICAL)
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_logger.setLevel(logging.CRITICAL)
zendriver_logger = logging.getLogger("zendriver")
zendriver_logger.setLevel(logging.CRITICAL)
nodriver_logger = logging.getLogger("nodriver")
nodriver_logger.setLevel(logging.CRITICAL)
ws_logger = logging.getLogger("websockets")
ws_logger.setLevel(logging.CRITICAL)
conn_logger = logging.getLogger("uc.connection")
conn_logger.setLevel(logging.CRITICAL)

logger = logger.bind(name="Xilriws")

if sys.platform != "win32":
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
# else:
#     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main(cion_mode: bool):
    if os.path.exists("config.json"):
        with open("config.json", "r") as f:
            config: dict[str, str | int] = json.load(f)
    else:
        config = {}

    ext_comm = ExtensionComm()
    task_creator.create_task(ext_comm.start())

    extenstion_paths = [
        config.get("proxy", "/xilriws/xilriws-proxy"),
        config.get("targetfp_path", "/xilriws/xilriws-targetfp"),
    ]

    if cion_mode:
        logger.info("Starting in Cion Mode")
        mode = CionMode(
            BrowserJoin(extension_paths=extenstion_paths, ext_comm=ext_comm)
        )
    else:
        proxies = ProxyDistributor(ext_comm)
        proxy_dispenser = ProxyDispenser(
            config.get("proxies_list_path", "/xilriws/proxies.txt")
        )

        mode = AuthMode(BrowserAuth(extension_paths=extenstion_paths, ext_comm=ext_comm, proxies=proxies), proxies, proxy_dispenser)

    await mode.prepare()

    port = config.get("port", 5090)
    host = config.get("host", "0.0.0.0")

    app = mode.get_litestar()
    server_config = uvicorn.Config(app, port=port, host=host, log_config=None)
    server = uvicorn.Server(server_config)

    logger.info(f"Starting Xilriws on http://{host}:{port}")

    await server.serve()


if __name__ == "__main__":
    asyncio.run(main(cion_mode=False))
