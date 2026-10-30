import logging
import sys

from pythonjsonlogger.json import JsonFormatter

from app.config import settings


def configure_logging():
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.LOG_LEVEL.upper())


logger = logging.getLogger("contextflow")