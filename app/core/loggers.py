import logging
import logging.config
from logging.handlers import TimedRotatingFileHandler

from .config import config as c


def setup_logging(log_level="INFO", use_basic_format=False):
    """
    Setup logging.
    Args:
        log_level (str): Log level name.
        use_basic_format (str): Use basic format.
    """
    configured_log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": (
                    "%(asctime)s %(levelname) s%(process)s %(processName)s "
                    "%(thread)s %(threadName) s%(name)s %(message)s"
                )
            },
            "basic": {
                "format":
                    "%(asctime)s %(levelname)s [%(process)d] "
                    "%(name)s %(message)s",
            }
        },
        "handlers": {
            "stdout": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default"
            },
            "stderr": {
                "level": "WARNING",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "formatter": "default"
            },
            "stdout-basic": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "basic"
            },
            "stderr-basic": {
                "level": "WARNING",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "formatter": "basic"
            },
        },
        "loggers": {
            "": {
                "level": log_level,
                "handlers": [
                    "stdout-basic" if use_basic_format else "stdout",
                    "stderr-basic" if use_basic_format else "stderr",
                ],
            },
        },
    }

    logging.config.dictConfig(configured_log_config)
