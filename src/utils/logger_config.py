"""logger_config.py: This module configures the logging.
This module uses structlog to configure logging.
"""

import logging
import sys
from typing import Literal

import structlog
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer


def configure_logger(
    logging_level: int
    | Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "FATAL"] = logging.INFO,
) -> None:
    """Configures the global logging settings for the application using structlog and Python's built-in logging module.

    This function applies various processors to the logs, including adding log level, logger name, and timestamp,
    rendering stack information, decoding unicode, and wrapping the message for formatter. The logs are output in
    both console and a file named "application.log". Console logs are formatted for readability while the file logs are
    in JSON format for further processing.

    It is recommended to call this function only once at the start of the application.

    Notes:
    -----
    The log level is set to INFO, meaning that INFO and above level logs (WARNING, ERROR, CRITICAL) are recorded.

    The configuration includes a `cache_logger_on_first_use` setting to improve performance by caching the logger
    on its first use.

    The standard output (stdout) and a file "application.log" are used as log outputs. If "application.log"
    already exists, new logs will be appended to the existing file.
    """
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S", utc=False),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    handler_stdout = logging.StreamHandler(sys.stdout)
    handler_stdout.setFormatter(structlog.stdlib.ProcessorFormatter(processor=ConsoleRenderer()))

    handler_file = logging.FileHandler("application.log")
    handler_file.setFormatter(structlog.stdlib.ProcessorFormatter(processor=JSONRenderer()))

    root_logger = logging.getLogger()
    root_logger.addHandler(handler_stdout)
    root_logger.addHandler(handler_file)
    match logging_level:
        case int():
            root_logger.setLevel(logging_level)
        case "DEBUG":
            root_logger.setLevel(logging.DEBUG)
        case "INFO":
            root_logger.setLevel(logging.INFO)
        case "WARNING":
            root_logger.setLevel(logging.WARNING)
        case "ERROR":
            root_logger.setLevel(logging.ERROR)
        case "CRITICAL", "FATAL":
            root_logger.setLevel(logging.CRITICAL)
        case _:
            root_logger.setLevel(logging.INFO)
