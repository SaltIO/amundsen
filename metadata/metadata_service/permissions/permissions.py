from http import HTTPStatus
import logging
from flask import jsonify, current_app
from functools import wraps


LOGGER = logging.getLogger(__name__)


def require_write_access(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # LOGGER.info(f"READ_ONLY_MODE={current_app.config.get('READ_ONLY_MODE', False)}")
        if current_app.config.get('READ_ONLY_MODE', False):
            return {
                "message": "API is in read-only mode. Write operations are not allowed."
            }, HTTPStatus.FORBIDDEN
        return f(*args, **kwargs)
    return wrapper
