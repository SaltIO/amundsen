# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from http import HTTPStatus
from typing import Any, Dict, Iterable, Mapping, Optional, Union

from flasgger import swag_from
from flask import request
from flask_restful import Resource, reqparse

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.lineage import LineageSchema, LineageBaseSchema
from amundsen_common.models.table import TableSchema
from amundsen_common.models.key_status import KeyStatusSchema
from amundsen_common.models.table import StatSchema

from marshmallow import ValidationError
from metadata_service.api import BaseAPI
from metadata_service.api.badge import BadgeCommon
from metadata_service.api.tag import TagCommon
from metadata_service.entity.dashboard_summary import DashboardSummarySchema
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client, BaseProxy
from ddp_auth.flask import require_auth


LOGGER = logging.getLogger(__name__)


class TableIdGET(BaseAPI):
    """
    TableIdGET API
    """

    def __init__(self) -> None:
        super().__init__(
            schema=TableSchema,
            str_type='table',
            client=get_proxy_client(),
            id_qstring_key='id'
        )

    @require_auth()
    @swag_from('swagger_doc/table/table_id_get.yml')
    def get(self, **kwargs: Optional[Any]) -> Iterable[Union[Mapping, int, None]]:
        return super().get(**kwargs)

class TableGET(BaseAPI):
    """
    TableGET API
    """

    def __init__(self) -> None:
        super().__init__(
            schema=TableSchema,
            str_type='table',
            client=get_proxy_client()
        )

    @require_auth()
    @swag_from('swagger_doc/table/table_get.yml')
    def get(self, *, database: str, cluster: str, schema: str, table: str) -> Iterable[Union[Mapping, int, None]]:
        return super().get(database=database, cluster=cluster, schema=schema, table=table)

class TablesGET(BaseAPI):
    """
    TablesGET supports GET operation to get multiple tables
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()
        super().__init__(TableSchema, 'tables', self.client)

    @require_auth()
    @swag_from('swagger_doc/table/tables_get.yml')
    def get(self, *, database: Optional[str] = None, cluster: Optional[str] = None, schema: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        return super().get(database=database, cluster=cluster, schema=schema)

class TablePutAPI(Resource):
    """
    TableDetail API
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()

    @require_auth('write:metadata')
    @swag_from('swagger_doc/table/detail_put.yml')
    def put(self) -> Iterable[Union[Mapping, int, None]]:
        data = None
        try:
            data = request.get_json(force=True)
            published_tag = data.pop('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            table = TableSchema().loads(json.dumps(data))

            table_key, status = self.client.create_update_table(table=table, published_tag=published_tag)

            result = KeyStatusSchema().dump({
                'key': table_key,
                'status': status
            })

            resp_code = HTTPStatus.CREATED if status == 'created' else HTTPStatus.OK

            return result, resp_code

        except ValidationError as ve:
            msg = 'Validation Error: {}'.format(ve.normalized_messages())
            return {'message': msg}, HTTPStatus.BAD_REQUEST

        except NotFoundException:
            return {'message': f'Failed to update/create table: {data}'}, HTTPStatus.NOT_FOUND


class TableLineageAPI(Resource):
    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('direction', type=str, location="args", required=False, default="both")
        self.parser.add_argument('depth', type=int, location="args", required=False, default=1)
        super(TableLineageAPI, self).__init__()

    @require_auth()
    @swag_from('swagger_doc/table/lineage_get.yml')
    def get(self, id: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        direction = args.get('direction')
        depth = args.get('depth')
        try:
            lineage = self.client.get_lineage(id=id,
                                              resource_type=ResourceType.Table,
                                              direction=direction,
                                              depth=depth)
            schema = LineageSchema()
            return schema.dump(lineage), HTTPStatus.OK
        except Exception as e:
            return {'message': f'Exception raised when getting table lineage: {e}'}, HTTPStatus.NOT_FOUND

    @require_auth('write:metadata')
    @swag_from('swagger_doc/table/lineage_put.yml')
    def put(self, id: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            data = request.get_json(force=True, silent=True) or {}

            lineage = data.get('lineage')
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)
            lineage['key'] = id

            lineage_base = LineageBaseSchema().loads(json.dumps(lineage))

            self.client.put_table_lineage(
                table_uri=id,
                lineage=lineage_base,
                published_tag=published_tag
            )

            return {}, HTTPStatus.OK

        except NotFoundException:
            msg = 'table_uri {} with column {} does not exist'.format(table_uri, column_name)
            return {'message': msg}, HTTPStatus.NOT_FOUND


class TableOwnerAPI(Resource):
    """
    TableOwner API to add / delete owner info
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()

    @require_auth('write:metadata')
    @swag_from('swagger_doc/table/owner_put.yml')
    def put(self, table_uri: str, owner: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            data = request.get_json(force=True, silent=True) or {}
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            self.client.add_owner(table_uri=table_uri, owner=owner, published_tag=published_tag)
            return {'message': 'The owner {} for table_uri {} '
                               'is added successfully'.format(owner,
                                                              table_uri)}, HTTPStatus.OK
        except Exception:
            return {'message': 'The owner {} for table_uri {} '
                               'is not added successfully'.format(owner,
                                                                  table_uri)}, HTTPStatus.INTERNAL_SERVER_ERROR

    @require_auth()
    @swag_from('swagger_doc/table/owner_delete.yml')
    def delete(self, table_uri: str, owner: str) -> Iterable[Union[Mapping, int, None]]:
        try:
            self.client.delete_owner(table_uri=table_uri, owner=owner)
            return {'message': 'The owner {} for table_uri {} '
                               'is deleted successfully'.format(owner,
                                                                table_uri)}, HTTPStatus.OK
        except Exception:
            return {'message': 'The owner {} for table_uri {} '
                               'is not deleted successfully'.format(owner,
                                                                    table_uri)}, HTTPStatus.INTERNAL_SERVER_ERROR


class TableDescriptionAPI(Resource):
    """
    TableDescriptionAPI supports PUT and GET operation to upsert table description
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(TableDescriptionAPI, self).__init__()

    @require_auth()
    @swag_from('swagger_doc/table/description_get.yml')
    def get(self, id: str) -> Iterable[Any]:
        """
        Returns description in Neo4j endpoint
        """
        try:
            description = self.client.get_table_description(table_uri=id)
            return {'description': description}, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'table_uri {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

        except Exception:
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @require_auth('write:metadata')
    @swag_from('swagger_doc/table/description_put.yml')
    def put(self, id: str) -> Iterable[Any]:
        """
        Updates table description (passed as a request body)
        :param table_uri:
        :return:
        """
        try:
            data = request.get_json(force=True, silent=True) or {}
            description = data.get('description')
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            self.client.put_table_description(table_uri=id, description=description, published_tag=published_tag)

            return {}, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'table_uri {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

class TableUpdateFrequencyAPI(Resource):
    """
    TableUpdateFrequencyAPI supports PUT and DELETE operation to table update frequency
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(TableUpdateFrequencyAPI, self).__init__()

    @require_auth('write:metadata')
    @swag_from('swagger_doc/table/update_frequency_put.yml')
    def put(self, table_uri: str) -> Iterable[Any]:
        """
        Updates table update freqeuency (passed as a request body)
        :param table_uri:
        :return:
        """
        try:
            data = request.get_json(force=True, silent=True) or {}
            frequency = data.get('frequency')
            published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

            self.client.put_table_update_frequency(table_uri=table_uri, frequency=frequency, published_tag=published_tag)
            return {}, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'table_uri {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

    @require_auth()
    @swag_from('swagger_doc/table/update_frequency_delete.yml')
    def delete(self, table_uri: str) -> Iterable[Any]:
        """
        Deletes table update frequency (passed as a request body)
        :param table_uri:
        :return:
        """
        try:
            self.client.delete_table_update_frequency(table_uri=table_uri)
            return {}, HTTPStatus.OK

        except NotFoundException:
            return {'message': 'table_uri {} does not exist'.format(id)}, HTTPStatus.NOT_FOUND

class TableTagAPI(Resource):
    """
    TableTagAPI that supports GET, PUT and DELETE operation to add or delete tag
    on table
    """

    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('tag_type', type=str, location="args", required=False, default='default')
        super(TableTagAPI, self).__init__()

        self._tag_common = TagCommon(client=self.client)

    @require_auth('write:metadata')
    @swag_from('swagger_doc/table/tag_put.yml')
    def put(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        """
        API to add a tag to existing table uri.

        :param table_uri:
        :param tag:
        :return:
        """
        args = self.parser.parse_args()
        # use tag_type to distinguish between tag and badge
        tag_type = args.get('tag_type', 'default')

        data = request.get_json(force=True, silent=True) or {}
        published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

        return self._tag_common.put(
            id=id,
            resource_type=ResourceType.Table,
            tag=tag,
            tag_type=tag_type,
            published_tag=published_tag
        )

    @require_auth()
    @swag_from('swagger_doc/table/tag_delete.yml')
    def delete(self, id: str, tag: str) -> Iterable[Union[Mapping, int, None]]:
        """
        API to remove a association between a given tag and a table.

        :param table_uri:
        :param tag:
        :return:
        """
        args = self.parser.parse_args()
        tag_type = args.get('tag_type', 'default')

        return self._tag_common.delete(id=id,
                                       resource_type=ResourceType.Table,
                                       tag=tag,
                                       tag_type=tag_type)


class TableBadgeAPI(Resource):
    def __init__(self) -> None:
        self.client = get_proxy_client()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('category', type=str, location="args", required=True)
        super(TableBadgeAPI, self).__init__()

        self._badge_common = BadgeCommon(client=self.client)

    @require_auth('write:metadata')
    @swag_from('swagger_doc/table/badge_put.yml')
    def put(self, id: str, badge: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        data = request.get_json(force=True, silent=True) or {}
        published_tag = data.get('published_tag', BaseProxy.DEFAULT_EDITED_PUBLISHED_TAG)

        return self._badge_common.put(
            id=id,
            resource_type=ResourceType.Table,
            badge_name=badge,
            category=category,
            published_tag=published_tag
        )

    @require_auth()
    @swag_from('swagger_doc/table/badge_delete.yml')
    def delete(self, id: str, badge: str) -> Iterable[Union[Mapping, int, None]]:
        args = self.parser.parse_args()
        category = args.get('category', '')

        return self._badge_common.delete(id=id,
                                         resource_type=ResourceType.Table,
                                         badge_name=badge,
                                         category=category)


class TableDashboardAPI(BaseAPI):
    """
    TableDashboard API that supports GET operation providing list of Dashboards using a table.
    """

    def __init__(self) -> None:
        super().__init__(
            schema=DashboardSummarySchema,
            str_type='resources_using_table',
            client=get_proxy_client()
        )

    @require_auth()
    @swag_from('swagger_doc/table/dashboards_using_table_get.yml')
    def get(self, *, id: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        return super().get(id=id, resource_type=ResourceType.Dashboard)

class TableStatsAPI(Resource):

    def __init__(self) -> None:
        self.client = get_proxy_client()
        super(TableStatsAPI, self).__init__()

    @require_auth()
    @swag_from('swagger_doc/table/stats_get.yml')
    def get(self, table_uri: str) -> Union[tuple, int, None]:
        """
        Gets table stats in Neo4j
        """
        try:
            LOGGER.info(f'TableStatsAPI:GET')
            stats = self.client.get_table_stats(table_uri=table_uri)
            LOGGER.info(f'stats={stats}')

            return {'table_stats': stats}, HTTPStatus.OK

        except NotFoundException:
            msg = 'table_uri {} does not exist'.format(table_uri)
            return {'message': msg}, HTTPStatus.NOT_FOUND

        except Exception:
            LOGGER.exception(f'FAILED')
            return {'message': 'Internal server error!'}, HTTPStatus.INTERNAL_SERVER_ERROR

    @require_auth('write:metadata')
    @swag_from('swagger_doc/table/stats_put.yml')
    def put(self,
            table_uri: str) -> Iterable[Union[dict, tuple, int, None]]:
        """
        Updates table stats (passed as a request body)
        :param table_uri:
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

                self.client.create_update_table_stats(
                    table_uri=table_uri,
                    stats=stats,
                    published_tag=published_tag
                )

                return {}, HTTPStatus.OK
            else:
                return {'message': f'No stats provided'}, HTTPStatus.BAD_REQUEST

        except ValidationError as ve:
            msg = 'Validation Error for table_uri {}: {}'.format(table_uri, ve.normalized_messages())
            return {'message': msg}, HTTPStatus.BAD_REQUEST
        except NotFoundException:
            msg = 'table_uri {} does not exist'.format(table_uri)
            return {'message': msg}, HTTPStatus.NOT_FOUND
