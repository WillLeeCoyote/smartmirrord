import logging
from logging.handlers import RotatingFileHandler

from smartmirrord.config import (
    LOG_LEVEL,
    LOG_TO_CONSOLE,
    LOG_TO_FILE,
    LOG_FILE_PATH,
    UART_DEBUG,
)


def setup_logging():
    root = logging.getLogger()
    root.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    if LOG_TO_CONSOLE:
        console = logging.StreamHandler()
        console.setFormatter(formatter)
        root.addHandler(console)

    if LOG_TO_FILE:
        file_handler = RotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    if UART_DEBUG:
        logging.getLogger("smartmirrord.hardware.uart_transport").setLevel(
            logging.DEBUG
        )
