# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import ast
from http import HTTPStatus
from typing import Any, Dict, Iterable, List, Mapping, Optional, Union

from flasgger import swag_from
from flask import request, current_app
from flask_restful import Resource

from metadata_service.auth import requires_auth, WRITE_PERMISSION

from amundsen_common.models.table import (
    Application, ApplicationSchema
)
from amundsen_common.models.key_status import KeyStatusSchema

from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client
from metadata_service.proxy.base_proxy import BaseProxy


LOGGER = logging.getLogger(__name__)


class ApplicationAPI(Resource):
    """
    Application API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(ApplicationAPI, self).__init__()

    @requires_auth()
    # @swag_from('swagger_doc/application/application_get.yml')
    def get(self, application_uri: str) -> Iterable[Union[Mapping, int, tuple, None]]:
        try:
            application = self.client.get_application(application_uri=application_uri)

            return {'application': application}, HTTPStatus.OK

        except NotFoundException:
            msg = 'application_uri {} does not exist'.format(application_uri)
            return {'message': msg}, HTTPStatus.NOT_FOUND

        except Exception:
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @requires_auth(required_permission=WRITE_PERMISSION)
    # @swag_from('swagger_doc/application/application_put.yml')
    def put(self) -> Iterable[Union[Mapping, int, tuple, None]]:
        try:
            data = request.get_json(force=True)  # Force parsing regardless of Content-Type

            if not data:
                return {'message': 'request json required'}, HTTPStatus.BAD_REQUEST

            if isinstance(data, str):  # If data is still a string, parse it manually
                data = json.loads(data)

            application = ApplicationSchema().load(data.get('application'))
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            application_key, status = self.client.create_update_application(
                application=application,
                published_tag=published_tag

            )

            result = KeyStatusSchema().dump({
                'key': application_key,
                'status': status
            })

            resp_code = HTTPStatus.CREATED if status == 'created' else HTTPStatus.OK

            return result, resp_code

        except Exception:
            LOGGER.exception("Application API Error: ")
            return {'message': 'internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR

