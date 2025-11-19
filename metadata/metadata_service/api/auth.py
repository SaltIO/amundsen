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
from ddp_auth.jwt import get_auth0_token


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
                LOGGER.warning("Auth token request missing client_id or client_secret")
                return {'message': 'client_id and client_secret required'}, HTTPStatus.BAD_REQUEST

            try:
                # Log Auth0 configuration (without secrets) for debugging
                import os
                auth0_domain = os.getenv('AUTH0_DOMAIN', 'NOT SET')
                auth0_audience = os.getenv('AUTH0_AUDIENCE', 'NOT SET')
                LOGGER.info(
                    f"Requesting Auth0 token: client_id={data['client_id'][:10]}..., "
                    f"domain={auth0_domain}, audience={auth0_audience}"
                )
                token_response = get_auth0_token(client_id=data['client_id'], client_secret=data['client_secret'])
                if not token_response:
                    LOGGER.error("get_auth0_token returned empty response")
                    return {'message': 'Token request returned empty response'}, HTTPStatus.INTERNAL_SERVER_ERROR
                LOGGER.debug("Auth0 token request successful")
                return token_response, HTTPStatus.OK
            except Exception as e:
                error_msg = str(e)
                LOGGER.error(
                    f"Auth0 token request failed: {error_msg}, "
                    f"domain={os.getenv('AUTH0_DOMAIN', 'NOT SET')}, "
                    f"audience={os.getenv('AUTH0_AUDIENCE', 'NOT SET')}",
                    exc_info=True
                )
                return {'message': str(e)}, HTTPStatus.UNAUTHORIZED

        except NotFoundException:
            LOGGER.exception("NotFoundException")
            return {'message': 'unable to auth'}, HTTPStatus.NOT_FOUND
        except Exception as e:
            LOGGER.exception(f"Unexpected error in auth endpoint: {str(e)}")
            return {'message': f'server error: {str(e)}'}, HTTPStatus.INTERNAL_SERVER_ERROR