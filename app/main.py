from app.adapters.inbound.http.app import create_app
from app.bootstrap.config import settings
from app.bootstrap.logging import setup_logging
from app.bootstrap.runtime import build_runtime

setup_logging(settings.LOG_LEVEL)
app = create_app(build_runtime(settings), settings)

__all__ = ["app"]
