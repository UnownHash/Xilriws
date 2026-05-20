from __future__ import annotations

import logging
import sys

from loguru import logger

from xilriws.config import config

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
    level=config.dev.log_level,
    filter=lambda record: record["level"].no < logging.ERROR,
    enqueue=True,
)
logger.add(sink=sys.stderr, format=console_format, colorize=True, level=logging.ERROR, backtrace=True, enqueue=True)
