# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import re
import logging
import textwrap
from typing import (Tuple)  # noqa: F401

import neo4j
from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.table import (User)

from metadata_service.proxy.neo4j_proxy import Neo4jProxy
from metadata_service.proxy.statsd_utilities import timer_with_counter
from metadata_service.util import UserResourceRel

LOGGER = logging.getLogger(__name__)

class Neo4jFabricProxy(Neo4jProxy):
    """
    A proxy to Neo4j (Gateway to Neo4j)
    """

    def __init__(self, *,
                 host: str,
                 port: int = 7687,
                 user: str = 'neo4j',
                 password: str = '',
                 num_conns: int = 50,
                 max_connection_lifetime_sec: int = 100,
                 encrypted: bool = False,
                 validate_ssl: bool = False,
                 database_name: str = neo4j.DEFAULT_DATABASE,
                 **kwargs: dict) -> None:
        super().__init__(
            host=host,
            port=port,
            user=user,
            password=password,
            num_conns=num_conns,
            max_connection_lifetime_sec=max_connection_lifetime_sec,
            encrypted=encrypted,
            validate_ssl=validate_ssl,
            database_name=database_name,
            kwargs=kwargs
        )
    
    def _prepare_return_statement(self, statement: str) -> str:
        cleaned_return_statement = "RETURN "
        return_statement = re.split('return ', statement, flags=re.IGNORECASE)[1]
        for column in return_statement.split(','):
            as_split = re.split(' as ', statement, flags=re.IGNORECASE)
            if len(as_split) == 1:
                cleaned_return_statement += as_split[0]
            else:
                cleaned_return_statement += as_split[1]

        return cleaned_return_statement

    def _fabric_query_statement(self, fabric_db_name: str, statement: str) -> str:
        fabric_statement = textwrap.dedent(f"""
            UNWIND {fabric_db_name}.graphIds() AS graphId
            CALL {{
                USE {fabric_db_name}.graph(graphId)
                {statement.replace(';','')}
            }}
            {self._prepare_return_statement(statement)}
        """)
        LOGGER.info(f"_fabric_query_statement={fabric_statement}")
        return fabric_statement

    def _get_col_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_col_query_statement())

    def _get_usage_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_usage_query_statement())

    def _get_table_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_table_query_statement())

    def _get_table_query_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_table_query_query_statement())

    def _get_description_query_statement(self, resource_type: ResourceType) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_description_query_statement(resource_type))

    def _get_column_description_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_column_description_query_statement())

    def _get_badge_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_badge_query_statement())

    def _get_tags_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_tags_query_statement())

    def _get_latest_updated_ts_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_latest_updated_ts_query_statement())

    def _get_statistics_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_statistics_query_statement())

    def _get_global_popular_resources_uris_query_statement(self, resource_type: ResourceType = ResourceType.Table) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_global_popular_resources_uris_query_statement(resource_type))

    def _get_personal_popular_resources_uris_query_statement(self, resource_type: ResourceType = ResourceType.Table) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_personal_popular_resources_uris_query_statement(resource_type))

    def _get_popular_tables_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_popular_tables_query_statement())

    def _get_popular_dashboards_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_popular_dashboards_query_statement())

    def _get_user_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_user_query_statement())

    def _get_users_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_users_query_statement())

    def _get_dashboard_by_user_relation_query_statement(self, user_email: str, relation_type: UserResourceRel) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_dashboard_by_user_relation_query_statement(user_email, relation_type))

    def _get_table_by_user_relation_query_statement(self, user_email: str, relation_type: UserResourceRel) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_table_by_user_relation_query_statement(user_email, relation_type))

    def _get_frequently_used_tables_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_frequently_used_tables_query_statement())

    def _get_dashboard_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_dashboard_query_statement())

    def _get_resources_using_table_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_resources_using_table_query_statement())

    def _get_both_lineage_query_statement(self, resource_type: ResourceType, depth: int = 1) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_both_lineage_query_statement(resource_type, depth))

    def _get_upstream_lineage_query_statement(self, resource_type: ResourceType, depth: int = 1) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_upstream_lineage_query_statement(resource_type, depth))

    def _get_downstream_lineage_query_statement(self, resource_type: ResourceType, depth: int = 1) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_downstream_lineage_query_statement(resource_type, depth))

    def _get_exec_feature_query_statement(self) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_exec_feature_query_statement())

    def _get_resource_generation_code_query_statement(self, resource_type: ResourceType) -> str:
        return self._fabric_query_statement('ddpfabric', super()._get_resource_generation_code_query_statement(resource_type))
    
    @timer_with_counter
    def put_resource_description(self, *,
                                 resource_type: ResourceType,
                                 uri: str,
                                 description: str) -> None:
        LOGGER.info('Neo4fFabricProxy is READ ONLY.  put_resource_description() is not supported')

    @timer_with_counter
    def put_column_description(self, *,
                               table_uri: str,
                               column_name: str,
                               description: str) -> None:
        LOGGER.info('Neo4fFabricProxy is READ ONLY.  put_column_description() is not supported')

    @timer_with_counter
    def add_resource_owner(self, *,
                           uri: str,
                           resource_type: ResourceType,
                           owner: str) -> None:
        LOGGER.info('Neo4fFabricProxy is READ ONLY.  add_resource_owner() is not supported')

    @timer_with_counter
    def delete_resource_owner(self, *,
                              uri: str,
                              resource_type: ResourceType,
                              owner: str) -> None:
        LOGGER.info('Neo4fFabricProxy is READ ONLY.  delete_resource_owner() is not supported')

    @timer_with_counter
    def add_badge(self, *,
                  id: str,
                  badge_name: str,
                  category: str = '',
                  resource_type: ResourceType) -> None:

        LOGGER.info('Neo4fFabricProxy is READ ONLY.  add_badge() is not supported')

    @timer_with_counter
    def delete_badge(self, id: str,
                     badge_name: str,
                     category: str,
                     resource_type: ResourceType) -> None:

        LOGGER.info('Neo4fFabricProxy is READ ONLY.  delete_badge() is not supported')

    @timer_with_counter
    def add_tag(self, *,
                id: str,
                tag: str,
                tag_type: str = 'default',
                resource_type: ResourceType = ResourceType.Table) -> None:
        LOGGER.info('Neo4fFabricProxy is READ ONLY.  add_tag() is not supported')

    @timer_with_counter
    def delete_tag(self, *,
                   id: str,
                   tag: str,
                   tag_type: str = 'default',
                   resource_type: ResourceType = ResourceType.Table) -> None:
        LOGGER.info('Neo4fFabricProxy is READ ONLY.  delete_tag() is not supported')

    def create_update_user(self, *, user: User) -> Tuple[User, bool]:
        LOGGER.info('Neo4fFabricProxy is READ ONLY.  create_update_user() is not supported')
    
    @timer_with_counter
    def add_resource_relation_by_user(self, *,
                                      id: str,
                                      user_id: str,
                                      relation_type: UserResourceRel,
                                      resource_type: ResourceType) -> None:
        LOGGER.info('Neo4fFabricProxy is READ ONLY.  add_resource_relation_by_user() is not supported')

    @timer_with_counter
    def delete_resource_relation_by_user(self, *,
                                         id: str,
                                         user_id: str,
                                         relation_type: UserResourceRel,
                                         resource_type: ResourceType) -> None:
        LOGGER.info('Neo4fFabricProxy is READ ONLY.  delete_resource_relation_by_user() is not supported')