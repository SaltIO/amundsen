# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
from http import HTTPStatus
from typing import Any, Iterable, Mapping, Optional, Union

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.data_source import DataProviderSchema, FileSchema
from flasgger import swag_from
from flask import request
from flask_restful import Resource, reqparse

from metadata_service.api import BaseAPI
from metadata_service.api.badge import BadgeCommon
from metadata_service.entity.description import DescriptionSchema
from metadata_service.api.tag import TagCommon
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client


class DataProviderDetailAPI(Resource):
    """
    DataProviderDetail API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    # @swag_from('swagger_doc/data_source/data_provider_get.yml')
    def get(self, data_provider_uri: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            data_provider = self.client.get_data_provider(data_provider_uri=data_provider_uri)
            schema = DataProviderSchema()
            return schema.dump(data_provider), HTTPStatus.OK

        except NotFoundException:
            return {'message': 'data_provider_uri {} does not exist'.format(data_provider_uri)}, HTTPStatus.NOT_FOUND

class FileDetailAPI(Resource):
    """
    FileDetailAPI API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    # @swag_from('swagger_doc/data_source/data_provider_get.yml')
    def get(self, file_uri: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            file = self.client.get_file(file_uri=file_uri)
            schema = FileSchema()
            return schema.dump(file), HTTPStatus.OK

        except NotFoundException:
            return {'message': 'data_prfile_uriovider_uri {} does not exist'.format(file_uri)}, HTTPStatus.NOT_FOUND

class FileLineageAPI(Resource):
    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('direction', type=str, required=False, default="both")
        self.parser.add_argument('depth', type=int, required=False, default=1)
        super(FileLineageAPI, self).__init__()

    # @swag_from('swagger_doc/table/lineage_get.yml')
    def get(self, id: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        direction = args.get('direction')
        depth = args.get('depth')
        try:
            lineage = self.client.get_lineage(id=id,
                                              resource_type=ResourceType.File,
                                              direction=direction,
                                              depth=depth)
            schema = LineageSchema()
            return schema.dump(lineage), HTTPStatus.OK
        except Exception as e:
            return {'message': f'Exception raised when getting lineage: {e}'}, HTTPStatus.NOT_FOUND
