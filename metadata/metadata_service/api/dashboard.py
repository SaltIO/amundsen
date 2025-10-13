# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from http import HTTPStatus
from typing import Iterable, Mapping, Optional, Union

from flasgger import swag_from
from flask import request
from flask_restful import Resource, reqparse

from marshmallow import ValidationError

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.dashboard import DashboardSchema
from amundsen_common.models.key_status import KeyStatusSchema

from metadata_service.api import BaseAPI
from metadata_service.api.badge import BadgeCommon
from metadata_service.api.tag import TagCommon
from metadata_service.entity.dashboard_detail import DashboardDetailSchema
from metadata_service.entity.description import DescriptionSchema
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client
from metadata_service.proxy.base_proxy import BaseProxy
from ddp_auth.flask import require_auth


LOGGER = logging.getLogger(__name__)


class DashboardDetailAPI(BaseAPI):
    """
    Dashboard detail API
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super().__init__(DashboardDetailSchema, 'dashboard', self.client)

    @require_auth()
    @swag_from('swagger_doc/dashboard/detail_get.yml')
    def get(self, *, id: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        try:
            return super().get(id=id)
        except NotFoundException:
            return {'message': 'dashboard_id {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

class DashboardPutAPI(BaseAPI):
    """
    Dashboard PUT API
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(DashboardPutAPI, self).__init__()

    @require_auth('write:metadata')
    @swag_from('swagger_doc/dashboard/detail_put.yml')
    def put(self) -> Iterable[Union[Mapping, int, None]]:
        data = None
        try:
            data = request.get_json(force=True)
            published_tag = data.pop('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            dashboard = DashboardSchema().loads(json.dumps(data))
            LOGGER.info(f'dashboard={dashboard}')

            dashboard_key, status = self.client.create_update_dashboard(
                dashboard=dashboard,
                published_tag=published_tag
            )

            result = KeyStatusSchema().dump({
                'key': dashboard_key,
                'status': status
            })

            resp_code = HTTPStatus.CREATED if status == 'created' else HTTPStatus.OK

            return result, resp_code

        except ValidationError as ve:
            msg = 'Validation Error: {}'.format(ve.normalized_messages())
            return {'message': msg}, HTTPStatus.BAD_REQUEST

        except NotFoundException:
            return {'message': f'Failed to update/create table: {data}'}, HTTPStatus.NOT_FOUND


class DashboardDescriptionAPI(BaseAPI):
    """
    DashboardDescriptionAPI supports PUT and GET operation to upsert table description
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super().__init__(DescriptionSchema, 'dashboard_description', self.client)

    @require_auth()
    @swag_from('swagger_doc/dashboard/description_get.yml')
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

    @require_auth('write:metadata')
    @swag_from('swagger_doc/dashboard/description_put.yml')
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

            self.client.put_dashboard_description(
                id=id,
                description=description,
                published_tag=published_tag
            )
            return {}, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'id {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND


class DashboardBadgeAPI(Resource):
    """
    DashboardBadgeAPI that supports PUT and DELETE operation to add or delete badges
    on Dashboard
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('category', type=str, location="args", required=True)
        super(DashboardBadgeAPI, self).__init__()

        self._badge_common = BadgeCommon(client=self.client)

    @require_auth('write:metadata')
    @swag_from('swagger_doc/dashboard/badge_put.yml')
    def put(self, id: str, badge: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        data = request.get_json(force=True, silent=True) or {}
        published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

        return self._badge_common.put(
            id=id,
            resource_type=ResourceType.Dashboard,
            badge_name=badge,
            category=category,
            published_tag=published_tag
        )

    @require_auth('write:metadata')
    @swag_from('swagger_doc/dashboard/badge_delete.yml')
    def delete(self, id: str, badge: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        return self._badge_common.delete(id=id,
                                         resource_type=ResourceType.Dashboard,
                                         badge_name=badge,
                                         category=category)


class DashboardTagAPI(Resource):
    """
    DashboardTagAPI that supports PUT and DELETE operation to add or delete tag
    on Dashboard
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('tag_type', type=str, location="args", required=False, default='default')
        super(DashboardTagAPI, self).__init__()

        self._tag_common = TagCommon(client=self.client)

    @require_auth('write:metadata')
    @swag_from('swagger_doc/dashboard/tag_put.yml')
    def put(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        """
        API to add a tag to existing Dashboard.

        :param table_uri:
        :param tag:
        :return:
        """
        args = self.parser.parse_args()
        tag_type = args.get('tag_type', 'default')

        data = request.get_json(force=True, silent=True) or {}
        published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

        return self._tag_common.put(
            id=id,
            resource_type=ResourceType.Dashboard,
            tag=tag,
            tag_type=tag_type,
            published_tag=published_tag
        )

    @require_auth('write:metadata')
    @swag_from('swagger_doc/dashboard/tag_delete.yml')
    def delete(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        """
        API to remove a association between a given tag and a Dashboard.

        :param table_uri:
        :param tag:
        :return:
        """
        args = self.parser.parse_args()
        tag_type = args.get('tag_type', 'default')

        return self._tag_common.delete(id=id,
                                       resource_type=ResourceType.Dashboard,
                                       tag=tag,
                                       tag_type=tag_type)

