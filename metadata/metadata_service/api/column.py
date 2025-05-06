# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import logging
import json
from http import HTTPStatus
from typing import Iterable, Mapping, Union

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.lineage import LineageSchema, LineageBaseSchema
from amundsen_common.models.table import StatSchema

from flasgger import swag_from
from flask import request
from flask_restful import Resource, reqparse

from metadata_service.api.badge import BadgeCommon
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client
from metadata_service.proxy.base_proxy import BaseProxy
from metadata_service.auth import requires_auth, WRITE_PERMISSION


LOGGER = logging.getLogger(__name__)


class ColumnLineageAPI(Resource):
    """
    ColumnLineageAPI supports GET operation to get column lineage
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('direction', type=str, location="args", required=False, default="both")
        self.parser.add_argument('depth', type=int, location="args", required=False, default=1)
        super(ColumnLineageAPI, self).__init__()

    @requires_auth()
    @swag_from('swagger_doc/column/lineage_get.yml')
    def get(self, table_uri: str, column_name: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        direction = args.get('direction')
        depth = args.get('depth')

        try:
            lineage = self.client.get_lineage(id=f"{table_uri}/{column_name}",
                                              resource_type=ResourceType.Column,
                                              direction=direction,
                                              depth=depth)
            schema = LineageSchema()
            return schema.dump(lineage), HTTPStatus.OK
        except Exception as e:
            return {'message': f'Exception raised when getting column lineage: {e}'}, HTTPStatus.NOT_FOUND

    @requires_auth(required_permission=WRITE_PERMISSION)
    @swag_from('swagger_doc/column/lineage_put.yml')
    def put(self, table_uri: str, column_name: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            data = json.loads(request.data)

            lineage = data.get('lineage')
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)
            lineage['key'] = table_uri + "/" + column_name

            lineage_base = LineageBaseSchema().loads(json.dumps(lineage))

            self.client.put_column_lineage(
                table_uri=table_uri,
                column_name=column_name,
                lineage=lineage_base,
                published_tag=published_tag
            )

            return {}, HTTPStatus.OK

        except NotFoundException:
            msg = 'table_uri {} with column {} does not exist'.format(table_uri, column_name)
            return {'message': msg}, HTTPStatus.NOT_FOUND


class ColumnDescriptionAPI(Resource):
    """
    ColumnDescriptionAPI supports PUT and GET operations to upsert column description
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(ColumnDescriptionAPI, self).__init__()

    @requires_auth(required_permission=WRITE_PERMISSION)
    @swag_from('swagger_doc/column/description_put.yml')
    def put(self,
            table_uri: str,
            column_name: str) -> Iterable[Union[dict, tuple, int, None]]:
        """
        Updates column description (passed as a request body)
        :param table_uri:
        :param column_name:
        :return:
        """
        try:
            data = json.loads(request.data)
            description = data.get('description')
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            self.client.put_column_description(
                table_uri=table_uri,
                column_name=column_name,
                description=description,
                published_tag=published_tag
            )

            return {}, HTTPStatus.OK

        except NotFoundException:
            msg = 'table_uri {} with column {} does not exist'.format(table_uri, column_name)
            return {'message': msg}, HTTPStatus.NOT_FOUND

    @requires_auth()
    @swag_from('swagger_doc/column/description_get.yml')
    def get(self, table_uri: str, column_name: str) -> Union[tuple, int, None]:
        """
        Gets column descriptions in Neo4j
        """
        try:
            description = self.client.get_column_description(table_uri=table_uri,
                                                             column_name=column_name)

            return {'description': description}, HTTPStatus.OK

        except NotFoundException:
            msg = 'table_uri {} with column {} does not exist'.format(table_uri, column_name)
            return {'message': msg}, HTTPStatus.NOT_FOUND

        except Exception:
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR


class ColumnBadgeAPI(Resource):
    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('category', type=str, location="args", required=True)
        super(ColumnBadgeAPI, self).__init__()

        self._badge_common = BadgeCommon(client=self.client)

    @requires_auth(required_permission=WRITE_PERMISSION)
    @swag_from('swagger_doc/column/badge_put.yml')
    def put(self, table_uri: str, badge: str, column_name: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        data = json.loads(request.data)
        published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

        return self._badge_common.put(
            id=f"{table_uri}/{column_name}",
            resource_type=ResourceType.Column,
            badge_name=badge,
            category=category,
            published_tag=published_tag
        )

    @requires_auth(required_permission=WRITE_PERMISSION)
    @swag_from('swagger_doc/column/badge_delete.yml')
    def delete(self, table_uri: str, badge: str, column_name: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        return self._badge_common.delete(id=f"{table_uri}/{column_name}",
                                         resource_type=ResourceType.Column,
                                         badge_name=badge,
                                         category=category)

class ColumnStatsAPI(Resource):

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(ColumnStatsAPI, self).__init__()

    @requires_auth()
    @swag_from('swagger_doc/column/stats_get.yml')
    def get(self, table_uri: str, column_name: str) -> Union[tuple, int, None]:
        """
        Gets column stats in Neo4j
        """
        try:
            LOGGER.info(f'ColumnStatsAPI:GET')
            stats = self.client.get_column_stats(table_uri=table_uri, column_name=column_name)
            LOGGER.info(f'stats={stats}')

            return {'column_stats': stats}, HTTPStatus.OK

        except NotFoundException:
            msg = 'table_uri {} with column {} does not exist'.format(table_uri, column_name)
            return {'message': msg}, HTTPStatus.NOT_FOUND

        except Exception:
            LOGGER.exception(f'FAILED')
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @requires_auth(required_permission=WRITE_PERMISSION)
    @swag_from('swagger_doc/column/stats_put.yml')
    def put(self,
            table_uri: str,
            column_name: str) -> Iterable[Union[dict, tuple, int, None]]:
        """
        Updates column description (passed as a request body)
        :param table_uri:
        :param column_name:
        :return:
        """

        try:
            data = request.get_json(force=True)
            _stats = data.get('stats')
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            if _stats and len(_stats) > 0:
                LOGGER.info(f'_stats={_stats}')
                stats = []
                for _stat in _stats:
                    LOGGER.info(f'_stat={json.dumps(_stat)}')
                    stats.append(StatSchema().loads(json.dumps(_stat)))

                self.client.create_update_column_stats(
                    table_uri=table_uri,
                    column_name=column_name,
                    stats=stats,
                    published_tag=published_tag
                )
            else:
                return {'message': f'No stats provided'}, HTTPStatus.BAD_REQUEST


        except NotFoundException:
            msg = 'table_uri {} with column {} does not exist'.format(table_uri, column_name)
            return {'message': msg}, HTTPStatus.NOT_FOUND

    # @requires_auth(required_permission=WRITE_PERMISSION)
    # # @swag_from('swagger_doc/column/badge_delete.yml')
    # def delete(self, table_uri: str, badge: str, column_name: str) -> Iterable[Union[Mapping, int, None]]:
    #     args = self.parser.parse_args()
    #     category = args.get('category', '')

    #     return self._badge_common.delete(id=f"{table_uri}/{column_name}",
    #                                      resource_type=ResourceType.Column,
    #                                      badge_name=badge,
    #                                      category=category)