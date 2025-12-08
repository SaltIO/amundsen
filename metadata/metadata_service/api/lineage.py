# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from http import HTTPStatus
from typing import Iterable, Mapping, Optional, Union

from flasgger import swag_from
from flask import request
from flask_restful import Resource, reqparse

from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client
from metadata_service.proxy.base_proxy import BaseProxy
from ddp_auth.flask_api_keys import require_auth


LOGGER = logging.getLogger(__name__)


class LineagePutAPI(Resource):
    """
    LineagePut API - Create bidirectional lineage between any two resources.
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('downstream_resource_key', type=str, required=True, location='args',
                                help='Downstream resource key is required as query parameter')

    @require_auth('write:metadata')
    @swag_from('swagger_doc/lineage/detail_put.yml')
    def put(self, upstream_resource_key: str) -> Iterable[Union[Mapping, int, None]]:
        """
        Create bidirectional lineage relationships between two resources.

        Creates:
        - downstream -> HAS_UPSTREAM -> upstream
        - upstream -> HAS_DOWNSTREAM -> downstream

        :param upstream_resource_key: Key of the upstream resource (from path)
        :return: Empty response on success
        """
        try:
            # Get downstream_resource_key from query parameter
            args = self.parser.parse_args()
            downstream_resource_key = args.get('downstream_resource_key')
            if not downstream_resource_key:
                return {'message': 'downstream_resource_key query parameter is required'}, HTTPStatus.BAD_REQUEST

            data = request.get_json(force=True, silent=True) or {}
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            self.client.create_lineage(
                upstream_resource_key=upstream_resource_key,
                downstream_resource_key=downstream_resource_key,
                published_tag=published_tag
            )

            return {}, HTTPStatus.OK

        except NotFoundException as e:
            return {'message': str(e)}, HTTPStatus.NOT_FOUND
        except ValueError as e:
            return {'message': str(e)}, HTTPStatus.BAD_REQUEST
        except Exception as e:
            LOGGER.exception('Failed to create lineage')
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR


class LineageDeleteAPI(Resource):
    """
    LineageDelete API - Delete bidirectional lineage between any two resources.
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('downstream_resource_key', type=str, required=True, location='args',
                                help='Downstream resource key is required as query parameter')

    @require_auth('write:metadata')
    @swag_from('swagger_doc/lineage/detail_delete.yml')
    def delete(self, upstream_resource_key: str) -> Iterable[Union[Mapping, int, None]]:
        """
        Delete bidirectional lineage relationships between two resources.

        Deletes:
        - downstream -> HAS_UPSTREAM -> upstream
        - upstream -> HAS_DOWNSTREAM -> downstream

        :param upstream_resource_key: Key of the upstream resource (from path)
        :return: Empty response on success
        """
        try:
            # Get downstream_resource_key from query parameter
            args = self.parser.parse_args()
            downstream_resource_key = args.get('downstream_resource_key')
            if not downstream_resource_key:
                return {'message': 'downstream_resource_key query parameter is required'}, HTTPStatus.BAD_REQUEST

            data = {}
            if request.data and len(request.data) > 0:
                try:
                    data = request.get_json(force=True, silent=True) or {}
                except Exception:
                    data = {}
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            self.client.delete_lineage(
                upstream_resource_key=upstream_resource_key,
                downstream_resource_key=downstream_resource_key,
                published_tag=published_tag
            )

            return {}, HTTPStatus.OK

        except NotFoundException as e:
            return {'message': str(e)}, HTTPStatus.NOT_FOUND
        except ValueError as e:
            return {'message': str(e)}, HTTPStatus.BAD_REQUEST
        except Exception as e:
            LOGGER.exception('Failed to delete lineage')
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR



