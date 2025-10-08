"""
# =============================================================================
# Script: utils.py
# Author: maxdaylight
# Last Updated: 2025-10-08 00:02:51 UTC
# Updated By: maxdaylight
# Version: 1.0.0
# Additional Info: Color output and logging utilities
# with ANSI stripping for files
# =============================================================================

Utilities for consistent colorized console output and structured logging
with UTC timestamps.
"""

from __future__ import annotations

import datetime
import logging
import os
import re
import socket
import sys

try:
    from colorama import Fore as _Fore
    from colorama import Style as _Style
    from colorama import init as colorama_init

    HAS_COLORAMA = True
    # Expose names for type checkers
    Fore = _Fore
    Style = _Style
    colorama_init(autoreset=True)
except Exception:  # pragma: no cover - optional dependency
    HAS_COLORAMA = False
    from typing import Any

    Fore = None
    Style = None

    def colorama_init(
        *args: Any, **kwargs: Any
    ) -> None:
        return None


ANSI_COLORS: dict[str, str] = {
    "reset": "\033[0m",
    "white": "\033[37m",
    "cyan": "\033[36m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "red": "\033[31m",
    "magenta": "\033[35m",
    "darkgray": "\033[90m",
}

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(s: str) -> str:
    return ANSI_RE.sub("", s)


def write_color_output(message: str, *, color: str = "white") -> None:
    """Write a message to stdout with the specified color.

    Ensures color reset to avoid bleeding. Falls back to plain text if color
    not supported.
    """

    color_key = color.lower()
    if HAS_COLORAMA:
        assert Fore is not None and Style is not None
        color_map = {
            "white": Fore.WHITE,
            "cyan": Fore.CYAN,
            "green": Fore.GREEN,
            "yellow": Fore.YELLOW,
            "red": Fore.RED,
            "magenta": Fore.MAGENTA,
            "darkgray": Fore.LIGHTBLACK_EX,
        }
        prefix = color_map.get(color_key, Fore.WHITE)
        print(f"{prefix}{message}{Style.RESET_ALL}")
    else:
        # If not TTY or on platforms without ANSI support, print plain text
        if sys.stdout.isatty():
            prefix = ANSI_COLORS.get(color_key, ANSI_COLORS["white"])
        else:
            prefix = ""
        reset = ANSI_COLORS["reset"] if prefix else ""
        print(f"{prefix}{message}{reset}")


class AnsiStrippingFileHandler(logging.FileHandler):
    def emit(
        self, record: logging.LogRecord
    ) -> None:
        if isinstance(record.msg, str):
            record.msg = strip_ansi(record.msg)
        super().emit(record)


def build_logger(
    name: str = "app",
    *,
    log_dir: str | None = None
) -> logging.Logger:
    """Create a logger that writes UTC timestamps and strips ANSI from files.

    The log file is named: {name}_{hostname}_{YYYY-MM-DD_HH-MM-SS}.log
    """

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # UTC ISO-like timestamps
    fmt = logging.Formatter(
        fmt="%(asctime)sZ %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt)
    logger.addHandler(console)

    host = socket.gethostname()
    ts = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d_%H-%M-%S")
    base_dir = log_dir or os.path.dirname(__file__)
    os.makedirs(base_dir, exist_ok=True)
    log_path = os.path.join(base_dir, f"{name}_{host}_{ts}.log")

    file_handler = AnsiStrippingFileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    logger.info("Logger initialized (UTC timestamps)")
    return logger
