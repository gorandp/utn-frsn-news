from .logger import get_logger


class Base():
    def __init__(self, name: str):
        self.logger = get_logger(name)
