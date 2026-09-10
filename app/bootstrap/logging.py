from __future__ import annotations

import logging

from app.application.ports import Telemetry


def setup_logging(level: str) -> None:
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))


class LoggingTelemetry:
    def __init__(self, logger_name: str = "rag_offline") -> None:
        self._logger = logging.getLogger(logger_name)

    def event(self, name: str, **attributes: object) -> None:
        self._logger.info("%s %s", name, attributes)


def telemetry() -> Telemetry:
    return LoggingTelemetry()
