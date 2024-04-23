# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
from http import HTTPStatus
from typing import Any, Iterable, Mapping, Optional, Union

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.data_source import DataProviderSchema, FileSchema
from amundsen_common.models.lineage import LineageSchema
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

class FileTagAPI(Resource):
    """
    FileTagAPI that supports PUT and DELETE operation to add or delete tag
    on File
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('tag_type', type=str, required=False, default='default')
        super(FileTagAPI, self).__init__()

        self._tag_common = TagCommon(client=self.client)

    # @swag_from('swagger_doc/tag/tag_put.yml')
    def put(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        """
        API to add a tag to existing File.

        :param file_uri:
        :param tag:
        :return:
        """
        args = self.parser.parse_args()
        tag_type = args.get('tag_type', 'default')

        return self._tag_common.put(id=id,
                                    resource_type=ResourceType.File,
                                    tag=tag,
                                    tag_type=tag_type)

    # @swag_from('swagger_doc/tag/tag_delete.yml')
    def delete(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        """
        API to remove a association between a given tag and a File.

        :param file_uri:
        :param tag:
        :return:
        """
        args = self.parser.parse_args()
        tag_type = args.get('tag_type', 'default')

        return self._tag_common.delete(id=id,
                                       resource_type=ResourceType.File,
                                       tag=tag,
                                       tag_type=tag_type)

class FileDescriptionAPI(BaseAPI):
    """
    FileDescriptionAPI supports PUT and GET operation to upsert file description
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super().__init__(DescriptionSchema, 'file_description', self.client)

    # @swag_from('swagger_doc/common/description_get.yml')
    def get(self, *, id: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        """
        Returns description
        """
        try:
            return super().get(id=id)

        except NotFoundException:
            return {'message': 'Dashboard {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

        except Exception:
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR

    # @swag_from('swagger_doc/common/description_put.yml')
    def put(self, id: str) -> Iterable[Union[Mapping, int, None]]:
        """
        Updates Dashboard description (passed as a request body)
        :param id:
        :return:
        """
        try:
            description = json.loads(request.data).get('description')
            self.client.put_file_description(id=id, description=description)
            return None, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'id {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

class FileOwnerAPI(Resource):
    """
    FileOwnerAPI API to add / delete owner info
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    # @swag_from('swagger_doc/file/owner_put.yml')
    def put(self, file_uri: str, owner: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            self.client.add_resource_owner(uri=file_uri, resource_type=ResourceType.File, owner=owner)
            return {'message': 'The owner {} for file_uri {} '
                               'is added successfully'.format(owner,
                                                              file_uri)}, HTTPStatus.OK
        except Exception:
            return {'message': 'The owner {} for file_uri {} '
                               'is not added successfully'.format(owner,
                                                                  file_uri)}, HTTPStatus.INTERNAL_SERVER_ERROR

    # @swag_from('swagger_doc/file/owner_delete.yml')
    def delete(self, file_uri: str, owner: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            self.client.delete_resource_owner(uri=file_uri, resource_type=ResourceType.File, owner=owner)
            return {'message': 'The owner {} for file_uri {} '
                               'is deleted successfully'.format(owner,
                                                                file_uri)}, HTTPStatus.OK
        except Exception:
            return {'message': 'The owner {} for file_uri {} '
                               'is not deleted successfully'.format(owner,
                                                                    file_uri)}, HTTPStatus.INTERNAL_SERVER_ERROR

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
