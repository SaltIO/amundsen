# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from http import HTTPStatus
from typing import Any, Iterable, Mapping, Optional, Union


from amundsen_common.models.auth import AuthTokenSchema
from flasgger import swag_from
from flask import request
from flask_restful import Resource, reqparse

from metadata_service.exception import NotFoundException
from metadata_service.auth import auth


LOGGER = logging.getLogger(__name__)


class AuthAPI(Resource):
    """
    Auth API
    """

    def __init__(self) -> None:
        pass

    @swag_from('swagger_doc/auth/token_post.yml')
    def post(self) -> Iterable[Union[Mapping, int, tuple, None]]:
        try:
            data = request.get_json(force=True)  # Force parsing regardless of Content-Type
            if isinstance(data, str):  # If data is still a string, parse it manually
                data = json.loads(data)
            if not data or 'client_id' not in data or 'client_secret' not in data:
                return {'message': 'client_id and client_secret required'}, 400

            auth_token = auth.get_token(client_id=data['client_id'], client_secret=data['client_secret'])
            schema = AuthTokenSchema()
            return schema.dump(auth_token), HTTPStatus.OK

        except NotFoundException:
            LOGGER.exception("NotFoundException")
            return {'message': 'unable to auth'}, HTTPStatus.NOT_FOUND
        except Exception:
            LOGGER.exception("Exception")
            return {'message': 'server error'}, HTTPStatus.INTERNAL_SERVER_ERROR