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

from amundsen_common.models.custom import (
    CustomMetadata, CustomMetadataSchema, CustomMetadataNode, CustomMetadataNodeSchema
)
from metadata_service.proxy import get_proxy_client
from metadata_service.proxy.base_proxy import BaseProxy


LOGGER = logging.getLogger(__name__)


class CustomMetadataPutAPI(Resource):
    """
    Custom Metadata Put API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(CustomMetadataPutAPI, self).__init__()

    @requires_auth(required_permission=WRITE_PERMISSION)
    # @swag_from('swagger_doc/reveal/chat_post.yml')
    def put(self) -> Iterable[Union[Mapping, int, tuple, None]]:
        try:
            data = request.get_json(force=True)  # Force parsing regardless of Content-Type

            if not data:
                return {'message': 'request json required'}, HTTPStatus.BAD_REQUEST

            if isinstance(data, str):  # If data is still a string, parse it manually
                data = json.loads(data)

            custom_metadata = CustomMetadataSchema().load(data.get('custom_metadata'))
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            custom_metadata_nodes: List[CustomMetadataNode] = self.client.create_update_custom_metadata(
                custom_metadata=custom_metadata,
                published_tag=published_tag

            )
            return CustomMetadataNodeSchema().dump(custom_metadata_nodes), HTTPStatus.OK

        except Exception:
            LOGGER.exception("Custom Metadata Put API Error: ")
            return {'message': 'internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR

