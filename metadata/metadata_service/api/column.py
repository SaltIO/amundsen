# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0
import logging
import json
from http import HTTPStatus
from typing import Iterable, Mapping, Optional, Union

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
from ddp_auth.flask_api_keys import require_auth

from marshmallow import ValidationError


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

    @require_auth()
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

    @require_auth('write:metadata')
    @swag_from('swagger_doc/column/lineage_put.yml')
    def put(self, table_uri: str, column_name: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            data = request.get_json(force=True, silent=True) or {}

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

    @require_auth('write:metadata')
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
            data = request.get_json(force=True, silent=True) or {}
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

    @require_auth()
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

    @require_auth('write:metadata')
    @swag_from('swagger_doc/column/badge_put.yml')
    def put(self, table_uri: str, badge: str, column_name: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        data = request.get_json(force=True, silent=True) or {}
        published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

        return self._badge_common.put(
            id=f"{table_uri}/{column_name}",
            resource_type=ResourceType.Column,
            badge_name=badge,
            category=category,
            published_tag=published_tag
        )

    @require_auth('write:metadata')
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

    @require_auth()
    @swag_from('swagger_doc/column/stats_get.yml')
    def get(self, table_uri: str, column_name: str) -> Union[tuple, int, None]:
        """
        Gets column stats in Neo4j
        """
        try:
            stats = self.client.get_column_stats(table_uri=table_uri, column_name=column_name)

            return {'column_stats': stats}, HTTPStatus.OK

        except NotFoundException:
            msg = 'table_uri {} with column {} does not exist'.format(table_uri, column_name)
            return {'message': msg}, HTTPStatus.NOT_FOUND

        except Exception:
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @require_auth('write:metadata')
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

                return {}, HTTPStatus.OK
            else:
                return {'message': f'No stats provided'}, HTTPStatus.BAD_REQUEST

        except ValidationError as ve:
            msg = 'Validation Error for table_uri {} with column {}: {}'.format(table_uri, column_name, ve.normalized_messages())
            return {'message': msg}, HTTPStatus.BAD_REQUEST
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


class ColumnDeleteAPI(Resource):
    """
    ColumnDelete API - Delete a column and all its directly connected orphaned nodes.
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()

    def _resolve_column_uri(
            self,
            column_uri: Optional[str] = None,
            table_name: Optional[str] = None,
            column_name: Optional[str] = None,
            database_name: Optional[str] = None,
            cluster_name: Optional[str] = None,
            schema_name: Optional[str] = None) -> str:
        """
        Resolve column URI from either:
        1. Direct column_uri parameter
        2. table_name + column_name + (database_name, cluster_name, schema_name) to lookup table

        Returns:
            Column URI (format: table_uri/column_name)

        Raises:
            NotFoundException: If table not found or multiple matches found
            ValueError: If required parameters are missing
        """
        if column_uri:
            return column_uri

        if not table_name or not column_name:
            raise ValueError('Either column_uri or (table_name and column_name) must be provided')

        # Lookup table by name using client's get_table method
        if database_name and cluster_name and schema_name:
            try:
                table = self.client.get_table(
                    database=database_name,
                    cluster=cluster_name,
                    schema=schema_name,
                    table=table_name
                )
                table_key = table.key
            except NotFoundException:
                raise NotFoundException(f'Table {table_name} not found in {database_name}://{cluster_name}.{schema_name}')
        else:
            # If not all table identifiers provided, try to find by name only
            # This may return multiple results, so we need to handle that
            raise ValueError('When using table_name, database_name, cluster_name, and schema_name are required to uniquely identify the table')

        # Build column URI
        return f"{table_key}/{column_name}"

    @require_auth('write:metadata')
    @swag_from('swagger_doc/column/detail_delete.yml')
    def delete(self, column_uri: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        """
        Delete a column and all its directly connected orphaned nodes.

        Can be called with:
        - column_uri: Direct column URI (format: table_uri/column_name)
        - OR table_name + column_name + (database_name, cluster_name, schema_name) in request body

        :param column_uri: Column URI (from path parameter)
        :return: Empty response with 200 OK on success
        """
        try:
            # Handle optional JSON body for table lookup
            data = {}
            if request.data and len(request.data) > 0:
                try:
                    data = request.get_json(force=True, silent=True) or {}
                except Exception:
                    data = {}
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            # Resolve column_uri
            resolved_column_uri = self._resolve_column_uri(
                column_uri=column_uri,
                table_name=data.get('table_name'),
                column_name=data.get('column_name'),
                database_name=data.get('database_name'),
                cluster_name=data.get('cluster_name'),
                schema_name=data.get('schema_name')
            )

            self.client.delete_column(column_uri=resolved_column_uri, published_tag=published_tag)

            return {}, HTTPStatus.OK

        except NotFoundException as e:
            return {'message': str(e)}, HTTPStatus.NOT_FOUND
        except ValueError as e:
            return {'message': str(e)}, HTTPStatus.BAD_REQUEST
        except Exception as e:
            LOGGER.exception('Failed to delete column')
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR


class ColumnPutAPI(Resource):
    """
    ColumnPut API - Create or update a column's properties.
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()

    def _resolve_column_uri(
            self,
            column_uri: Optional[str] = None,
            table_name: Optional[str] = None,
            column_name: Optional[str] = None,
            database_name: Optional[str] = None,
            cluster_name: Optional[str] = None,
            schema_name: Optional[str] = None) -> str:
        """
        Resolve column URI from either:
        1. Direct column_uri parameter
        2. table_name + column_name + (database_name, cluster_name, schema_name) to lookup table

        Returns:
            Column URI (format: table_uri/column_name)

        Raises:
            NotFoundException: If table not found or multiple matches found
            ValueError: If required parameters are missing
        """
        if column_uri:
            return column_uri

        if not table_name or not column_name:
            raise ValueError('Either column_uri or (table_name and column_name) must be provided')

        # Lookup table by name using client's get_table method
        if database_name and cluster_name and schema_name:
            try:
                table = self.client.get_table(
                    database=database_name,
                    cluster=cluster_name,
                    schema=schema_name,
                    table=table_name
                )
                table_key = table.key
            except NotFoundException:
                raise NotFoundException(f'Table {table_name} not found in {database_name}://{cluster_name}.{schema_name}')
        else:
            # If not all table identifiers provided, try to find by name only
            # This may return multiple results, so we need to handle that
            raise ValueError('When using table_name, database_name, cluster_name, and schema_name are required to uniquely identify the table')

        # Build column URI
        return f"{table_key}/{column_name}"

    @require_auth('write:metadata')
    @swag_from('swagger_doc/column/detail_put.yml')
    def put(self, column_uri: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        """
        Create or update a column's properties (name, type, sort_order).

        Can be called with:
        - column_uri: Direct column URI (format: table_uri/column_name) in path
        - OR table_name + column_name + (database_name, cluster_name, schema_name) in request body

        :param column_uri: Column URI (from path parameter)
        :return: Empty response with 200 OK on success
        """
        try:
            data = request.get_json(force=True, silent=True) or {}
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            # Resolve column_uri
            resolved_column_uri = self._resolve_column_uri(
                column_uri=column_uri,
                table_name=data.get('table_name'),
                column_name=data.get('column_name'),
                database_name=data.get('database_name'),
                cluster_name=data.get('cluster_name'),
                schema_name=data.get('schema_name')
            )

            # Extract column properties from request body
            col_type = data.get('col_type')
            sort_order = data.get('sort_order')
            column_name_for_create = data.get('column_name')  # For creation if column doesn't exist

            self.client.create_update_column(
                column_uri=resolved_column_uri,
                column_name=column_name_for_create,
                col_type=col_type,
                sort_order=sort_order,
                published_tag=published_tag
            )

            return {}, HTTPStatus.OK

        except NotFoundException as e:
            return {'message': str(e)}, HTTPStatus.NOT_FOUND
        except ValueError as e:
            return {'message': str(e)}, HTTPStatus.BAD_REQUEST
        except Exception as e:
            LOGGER.exception('Failed to create/update column')
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR