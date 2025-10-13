# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
from http import HTTPStatus
from typing import Any, Iterable, Mapping, Optional, Union
import logging

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.data_source import DataProviderSchema, FileSchema
from amundsen_common.models.lineage import LineageSchema
from amundsen_common.models.key_status import KeyStatusSchema
from flasgger import swag_from
from flask import request
from flask_restful import Resource, reqparse
from marshmallow import ValidationError

from metadata_service.api import BaseAPI
from metadata_service.api.badge import BadgeCommon
from metadata_service.entity.description import DescriptionSchema
from metadata_service.api.tag import TagCommon
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client
from metadata_service.proxy.base_proxy import BaseProxy
from ddp_auth.flask import require_auth


LOGGER = logging.getLogger(__name__)


class DataProviderDetailAPI(Resource):
    """
    DataProviderDetail API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @require_auth()
    # @swag_from('swagger_doc/data_source/data_provider_get.yml')
    def get(self, data_provider_uri: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            data_provider = self.client.get_data_provider(data_provider_uri=data_provider_uri)
            schema = DataProviderSchema()
            return schema.dump(data_provider), HTTPStatus.OK

        except NotFoundException:
            return {'message': 'data_provider_uri {} does not exist'.format(data_provider_uri)}, HTTPStatus.NOT_FOUND

class DataProviderDescriptionAPI(BaseAPI):
    """
    DataProviderDescriptionAPI supports PUT and GET operation to upsert data provider description
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super().__init__(DescriptionSchema, 'data_provider_description', self.client)

    @require_auth()
    # @swag_from('swagger_doc/common/description_get.yml')
    def get(self, *, id: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        """
        Returns description
        """
        try:
            return super().get(id=id)

        except NotFoundException:
            return {'message': 'Data Provider {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

        except Exception:
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @require_auth('write:metadata')
    # @swag_from('swagger_doc/common/description_put.yml')
    def put(self, id: str) -> Iterable[Union[Mapping, int, None]]:
        """
        Updates Data Provider description (passed as a request body)
        :param id:
        :return:
        """
        try:
            data = request.get_json(force=True, silent=True) or {}
            description = data.get('description')
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            self.client.put_data_provider_description(
                id=id,
                description=description,
                published_tag=published_tag
            )

            return {}, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'id {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

class FileDetailAPI(Resource):
    """
    FileDetailAPI API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @require_auth()
    @swag_from('swagger_doc/data_source/file_get.yml')
    def get(self, file_uri: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            file = self.client.get_file(file_uri=file_uri)
            return FileSchema().dump(file), HTTPStatus.OK

        except NotFoundException:
            return {'message': 'data_prfile_uriovider_uri {} does not exist'.format(file_uri)}, HTTPStatus.NOT_FOUND


class FilePutAPI(Resource):
    """
    FilePutAPI that supports PUT and DELETE operation
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(FilePutAPI, self).__init__()

    @require_auth('write:metadata')
    @swag_from('swagger_doc/data_source/file_put.yml')
    def put(self) -> Iterable[Union[Mapping, int, None]]:
        data = None
        try:
            data = request.get_json(force=True)
            published_tag = data.pop('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            file = FileSchema().loads(json.dumps(data))

            file_key_key, status = self.client.create_update_file(
                file=file,
                published_tag=published_tag
            )

            result = KeyStatusSchema().dump({
                'key': file_key_key,
                'status': status
            })

            resp_code = HTTPStatus.CREATED if status == 'created' else HTTPStatus.OK

            return result, resp_code

        except ValidationError as ve:
            msg = 'Validation Error: {}'.format(ve.normalized_messages())
            return {'message': msg}, HTTPStatus.BAD_REQUEST

        except NotFoundException:
            return {'message': f'Failed to update/create file: {data}'}, HTTPStatus.NOT_FOUND

class FileTagAPI(Resource):
    """
    FileTagAPI that supports PUT and DELETE operation to add or delete tag
    on File
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('tag_type', type=str, location="args", required=False, default='default')
        super(FileTagAPI, self).__init__()

        self._tag_common = TagCommon(client=self.client)

    @require_auth('write:metadata')
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

        data = request.get_json(force=True, silent=True) or {}
        published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

        return self._tag_common.put(
            id=id,
            resource_type=ResourceType.File,
            tag=tag,
            tag_type=tag_type,
            published_tag=published_tag
        )

    @require_auth()
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

    @require_auth()
    # @swag_from('swagger_doc/common/description_get.yml')
    def get(self, *, id: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        """
        Returns description
        """
        try:
            return super().get(id=id)

        except NotFoundException:
            return {'message': 'File {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

        except Exception:
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @require_auth('write:metadata')
    # @swag_from('swagger_doc/common/description_put.yml')
    def put(self, id: str) -> Iterable[Union[Mapping, int, None]]:
        """
        Updates Dashboard description (passed as a request body)
        :param id:
        :return:
        """
        try:
            data = request.get_json(force=True, silent=True) or {}
            description = data.get('description')
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            self.client.put_file_description(
                id=id,
                description=description,
                published_tag=published_tag
            )

            return {}, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'id {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

class FileOwnerAPI(Resource):
    """
    FileOwnerAPI API to add / delete owner info
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @require_auth('write:metadata')
    # @swag_from('swagger_doc/file/owner_put.yml')
    def put(self, file_uri: str, owner: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            data = request.get_json(force=True, silent=True) or {}
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            self.client.add_resource_owner(
                uri=file_uri,
                resource_type=ResourceType.File,
                owner=owner,
                published_tag=published_tag
            )

            return {'message': 'The owner {} for file_uri {} '
                               'is added successfully'.format(owner,
                                                              file_uri)}, HTTPStatus.OK
        except Exception:
            return {'message': 'The owner {} for file_uri {} '
                               'is not added successfully'.format(owner,
                                                                  file_uri)}, HTTPStatus.INTERNAL_SERVER_ERROR

    @require_auth()
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
        self.parser.add_argument('direction', type=str, location="args", required=False, default="both")
        self.parser.add_argument('depth', type=int, location="args", required=False, default=1)
        super(FileLineageAPI, self).__init__()

    @require_auth()
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
            return {'message': f'Exception raised when getting file lineage: {e}'}, HTTPStatus.NOT_FOUND

