from __future__ import annotations

import logging
import sys

from loguru import logger
from .debug import IS_DEBUG

console_format = " | ".join(
    (
        "<cyan>{time:HH:mm:ss.SS}</cyan>",
        "<level>{level: >1.1}</level>",
        "<cyan>{extra[name]: <18.18}</cyan>",
        "<level>{message}</level>",
    )
)

logger.remove()

logger.add(
    sink=sys.stdout,
    format=console_format,
    colorize=True,
    level=logging.DEBUG if IS_DEBUG else logging.INFO,
    filter=lambda record: record["level"].no < logging.ERROR,
    enqueue=True,
)
logger.add(sink=sys.stderr, format=console_format, colorize=True, level=logging.ERROR, backtrace=True, enqueue=True)
