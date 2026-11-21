"""Shared logging configuration for the API test suite."""

import logging
import sys
from pathlib import Path


def get_logger(name):
    """Return a named logger configured for console and file output."""

    try:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
    except OSError as error:
        raise RuntimeError(
            f"Unable to create or access the logs directory: {error}"
        ) from error

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            file_handler = logging.FileHandler(
                log_dir / "restful_booker.log",
                mode="a",
                encoding="utf-8",
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (OSError, ValueError) as error:
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()
            raise RuntimeError(
                f"Unable to configure logger '{name}': {error}"
            ) from error

    return logger
