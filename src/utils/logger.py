"""Configuración centralizada de logging con colores y múltiples handlers."""

from __future__ import annotations

import logging
from logging import Handler
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

try:
    from colorlog import ColoredFormatter
except ImportError:  # pragma: no cover
    ColoredFormatter = None  # type: ignore


LOG_FORMAT = "%(log_color)s[%(levelname)s]%(reset)s %(asctime)s - %(name)s - %(message)s"
PLAIN_FORMAT = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s"


def _build_console_handler(level: int) -> Handler:
    """Crea un handler de consola con formato coloreado si es posible."""

    console = logging.StreamHandler()
    console.setLevel(level)

    if ColoredFormatter is not None:
        formatter = ColoredFormatter(
            LOG_FORMAT,
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    else:
        formatter = logging.Formatter(PLAIN_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    console.setFormatter(formatter)
    return console


def _build_file_handler(path: Path, level: int, max_bytes: int, backup_count: int) -> Handler:
    """Crea un handler rotatorio conectado a archivo."""

    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(path, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(PLAIN_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))
    return handler


def configure_logging(
    *,
    level: int = logging.INFO,
    console: bool = True,
    logfile: Optional[Path] = None,
    max_bytes: int = 2 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """Configura el logging global del proyecto."""

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Limpiar handlers previos para evitar duplicados.
    root_logger.handlers.clear()

    if console:
        root_logger.addHandler(_build_console_handler(level))

    if logfile is not None:
        root_logger.addHandler(_build_file_handler(logfile, level, max_bytes, backup_count))


def get_logger(name: str) -> logging.Logger:
    """Devuelve un logger listo para usar. Configura defaults si es necesario."""

    logger = logging.getLogger(name)
    if not logging.getLogger().handlers:
        # Configuración por defecto si nadie la ha hecho todavía.
        configure_logging()
    return logger


# Configuración inicial recomendada cuando se importe el módulo.
configure_logging()


