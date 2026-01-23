# -*- coding: utf-8 -*-
"""Logging helpers for consistent output across modules."""

from __future__ import annotations

import logging
import os


def configure_logging() -> None:
    level_name = os.getenv("ZYNTALIC_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        )
    else:
        root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)
