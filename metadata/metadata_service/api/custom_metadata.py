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

from ddp_auth.flask import require_auth

from amundsen_common.models.custom import (
    CustomMetadata, CustomMetadataSchema, CustomMetadataNode, CustomMetadataNodeSchema
)
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client
from metadata_service.proxy.base_proxy import BaseProxy


LOGGER = logging.getLogger(__name__)


class CustomMetadataAPI(Resource):
    """
    Custom Metadata Put API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(CustomMetadataAPI, self).__init__()

    @require_auth()
    # @swag_from('swagger_doc/custom_metadata/custom_metadata_get.yml')
    def get(self, label: str, custom_metadata_uri: Optional[str] = None) -> Iterable[Union[Mapping, int, tuple, None]]:
        try:
            custom_metadata = self.client.get_custom_metadata(
                label=label,
                custom_metadata_uri=custom_metadata_uri
            )

            return {'custom_metadata': custom_metadata}, HTTPStatus.OK

        except NotFoundException:
            msg = 'custom_metadata_uri {} does not exist'.format(custom_metadata_uri)
            return {'message': msg}, HTTPStatus.NOT_FOUND

        except Exception:
            LOGGER.exception("Fail:")
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @require_auth('write:metadata')
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

            return CustomMetadataNodeSchema().dump(custom_metadata_nodes, many=True), HTTPStatus.OK

        except Exception:
            LOGGER.exception("Custom Metadata Put API Error: ")
            return {'message': 'internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR

