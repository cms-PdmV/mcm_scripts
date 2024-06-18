"""
This module configures the library logger,
its message format and its level.
"""

import logging
import sys


class LoggerFactory:
    _instances: dict[str, logging.Logger] = {}

    @classmethod
    def _create_logger(cls, name: str) -> logging.Logger:
        logger = logging.getLogger(name=name)
        if not logger.hasHandlers():
            format = "[%(asctime)s][%(levelname)s][%(name)s]: %(message)s"
            date_format = "%Y-%m-%d %H:%M:%S %z"
            handler = logging.StreamHandler(stream=sys.stdout)
            formatter = logging.Formatter(fmt=format, datefmt=date_format)

            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    @classmethod
    def getLogger(cls, name: str) -> logging.Logger:
        logger = cls._instances.get(name)
        if logger:
            return logger

        logger = cls._create_logger(name)
        cls._instances[name] = logger
        return logger
