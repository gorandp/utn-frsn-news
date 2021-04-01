import os
import logging


LOGGER_LEVEL = getattr(logging, os.getenv('LOGGER_LEVEL'))
LOGGER_FORMAT_STR_HEAD = '%(asctime)s [%(log_name)s][%(levelname)s] %(message)s'


def get_logger(log_name: str) -> logging.LoggerAdapter:
    logger = logging.getLogger(name=log_name)

    logger_format_str = LOGGER_FORMAT_STR_HEAD
    extra = {'log_name': log_name}
    l_format = logging.Formatter(logger_format_str)

    if logger.hasHandlers():
        # Returns a currently existing logger with the same log_name
        logger = logging.LoggerAdapter(logger, extra)
        return logger

    c_handler = logging.StreamHandler()
    c_handler.setFormatter(l_format)
    logger.addHandler(c_handler)

    logger.setLevel(LOGGER_LEVEL)
    logger = logging.LoggerAdapter(logger, extra)

    return logger
