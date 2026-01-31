import sys
import logging


class LoggerConfig:
    LOGGER_LEVEL = logging.INFO
    LOGGER_FORMAT_STR_HEAD = "[%(log_name)s:%(levelname)s] - %(asctime)s - %(message)s"

    @classmethod
    def set_level(cls, level: str | None) -> None:
        cls.LOGGER_LEVEL = getattr(
            logging,
            level or "INFO",
            logging.INFO,
        )


def get_logger(log_name: str) -> logging.LoggerAdapter:
    logger = logging.getLogger(name=log_name)

    logger_format_str = LoggerConfig.LOGGER_FORMAT_STR_HEAD
    extra = {"log_name": log_name}
    l_format = logging.Formatter(logger_format_str)

    if logger.hasHandlers():
        # Returns a currently existing logger with the same log_name
        logger = logging.LoggerAdapter(logger, extra)
        return logger

    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setFormatter(l_format)
    logger.addHandler(c_handler)

    logger.setLevel(LoggerConfig.LOGGER_LEVEL)
    logger = logging.LoggerAdapter(logger, extra)

    return logger


class LogWrapper:
    def __init__(self, log_name: str | None = None) -> None:
        self.logger = get_logger(log_name or self.__module__)
