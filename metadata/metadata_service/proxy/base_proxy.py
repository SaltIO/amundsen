# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from flask import current_app as app
from abc import ABCMeta, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.api.health_check import HealthCheck
from amundsen_common.models.dashboard import DashboardSummary, Dashboard
from amundsen_common.models.feature import Feature
from amundsen_common.models.generation_code import GenerationCode
from amundsen_common.models.lineage import Lineage, LineageBase
from amundsen_common.models.popular_table import PopularTable
from amundsen_common.models.table import Table, Stat, Application
from amundsen_common.models.data_source import DataProvider, File
from amundsen_common.models.user import User
from amundsen_common.models.snowflake.snowflake import SnowflakeTableShare
from amundsen_common.models.database import Database
from amundsen_common.models.cluster import Cluster
from amundsen_common.models.custom import CustomMetadata, CustomMetadataNode

from metadata_service.entity.dashboard_detail import \
    DashboardDetail as DashboardDetailEntity
from metadata_service.entity.description import Description
from metadata_service.util import UserResourceRel
from metadata_service.proxy.snowflake_base_proxy import SnowflakeBaseProxy


class BaseProxy(SnowflakeBaseProxy, metaclass=ABCMeta):

    DEFAULT_EDITED_PUBLISHED_TAG = "edited"

    """
    Base Proxy, which behaves like an interface for all
    the proxy clients available in the amundsen metadata service
    """
    def _get_user_details(self, user_id: str, user_data: Optional[Dict] = None) -> Dict:
        """
        Helper function to help get the user details if the `USER_DETAIL_METHOD` is configured,
        else uses the user_id for both email and user_id properties.
        :param user_id: The Unique user id of a user entity
        :return: a dictionary of user details
        """
        if app.config.get('USER_DETAIL_METHOD'):
            user_details = app.config.get('USER_DETAIL_METHOD')(user_id)  # type: ignore
        elif user_data:
            user_details = user_data
        else:
            user_details = {'email': user_id, 'user_id': user_id}

        return user_details

    def health(self) -> HealthCheck:
        return HealthCheck(status='ok', checks={f'{type(self).__name__}:connection': {'status': 'not checked'}})

    @abstractmethod
    def get_user(self, *, id: str) -> Union[User, None]:
        pass

    @abstractmethod
    def create_update_user(self, *, user: User, published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> Tuple[User, bool]:
        """
        Allows creating and updating users. Returns a tuple of the User
        object that has been created or updated as well as a flag that
        depicts whether or no the user was created or updated.

        :param user: a User object
        :return: Tuple of [User object, bool (True = created, False = updated)]
        """
        pass

    @abstractmethod
    def get_users(self) -> List[User]:
        pass

    @abstractmethod
    def get_table(self, *, id: str) -> Table:
        pass

    @abstractmethod
    def get_tables(self, *, database: Optional[str] = None, cluster: Optional[str] = None, schema: Optional[str] = None) -> List[Table]:
        pass

    @abstractmethod
    def create_update_table(
            self,
            *,
            table: Table,
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def delete_table(
            self,
            *,
            table_uri: str,
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        """
        Delete a table and all its child resources (columns, descriptions, stats, etc.).

        :param table_uri: Table URI (key in Neo4j)
        :param published_tag: Published tag for audit trail
        """
        pass

    @abstractmethod
    def create_update_dashboard(
            self,
            *,
            dashboard: Dashboard,
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def create_update_file(
            self,
            *,
            file: File,
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass


    @abstractmethod
    def delete_owner(self, *, table_uri: str, owner: str) -> None:
        pass

    @abstractmethod
    def add_owner(self, *, table_uri: str, owner: str, published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def get_table_description(self, *,
                              table_uri: str) -> Union[str, None]:
        pass

    @abstractmethod
    def put_table_description(self, *,
                              table_uri: str,
                              description: str,
                              published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def delete_table_description(self, *,
                                 table_uri: str,
                                 published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def delete_resource_description(self, *,
                                    resource_type: ResourceType,
                                    uri: str,
                                    published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def patch_table_properties(self, *,
                              table_uri: str,
                              properties: Dict[str, Any],
                              published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        """
        Update specific table properties in Neo4j.

        :param table_uri: Table URI (key in Neo4j)
        :param properties: Dictionary of property names to values to update
        :param published_tag: Published tag for audit trail
        """
        pass

    @abstractmethod
    def put_table_update_frequency(self, *,
                              table_uri: str,
                              frequency: str,
                              published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def put_table_lineage(
            self, *,
            table_uri: str,
            lineage: LineageBase,
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def delete_table_update_frequency(self, *,
                                      table_uri: str) -> None:
        pass

    @abstractmethod
    def add_tag(self, *, id: str, tag: str, tag_type: str, resource_type: ResourceType, published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def update_tag(self, *, old_tag: str, old_tag_type: str, new_tag: str, new_tag_type: str) -> None:
        pass

    @abstractmethod
    def add_badge(self, *, id: str, badge_name: str, category: str = '',
                  resource_type: ResourceType, published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def delete_tag(self, *, id: str, tag: str, tag_type: str, resource_type: ResourceType) -> None:
        pass

    @abstractmethod
    def delete_badge(self, *, id: str, badge_name: str, category: str,
                     resource_type: ResourceType) -> None:
        pass

    @abstractmethod
    def put_column_lineage(
            self, *,
            table_uri: str,
            column_name: str,
            lineage: LineageBase,
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def put_column_description(self, *,
                               table_uri: str,
                               column_name: str,
                               description: str,
                               published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def get_column_description(self, *,
                               table_uri: str,
                               column_name: str) -> Union[str, None]:
        pass

    @abstractmethod
    def put_type_metadata_description(self, *,
                                      type_metadata_key: str,
                                      description: str,
                                      published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def get_type_metadata_description(self, *,
                                      type_metadata_key: str) -> Union[str, None]:
        pass

    @abstractmethod
    def get_popular_tables(self, *,
                           num_entries: int,
                           user_id: Optional[str] = None) -> List[PopularTable]:
        pass

    @abstractmethod
    def get_popular_resources(self, *,
                              num_entries: int,
                              resource_types: List[str],
                              user_id: Optional[str] = None) -> Dict[str, List]:
        raise NotImplementedError

    @abstractmethod
    def get_latest_updated_ts(self) -> int:
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_tags(self) -> List:
        pass

    @abstractmethod
    def get_badges(self) -> List:
        pass

    @abstractmethod
    def get_dashboard_by_user_relation(self, *, user_email: str, relation_type: UserResourceRel) \
            -> Dict[str, List[DashboardSummary]]:
        pass

    @abstractmethod
    def get_table_by_user_relation(self, *, user_email: str,
                                   relation_type: UserResourceRel) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_column_stats(self, *,
                         table_uri: str,
                         column_name: str) -> List:
        pass

    @abstractmethod
    def create_update_column_stats(
            self,
            *,
            table_uri: str,
            column_name: str,
            stats: List[Stat],
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def delete_column(
            self,
            *,
            column_uri: str,
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        """
        Delete a column and all its directly connected orphaned nodes.

        This method performs cascading deletion:
        - Deletes column description relationships and orphaned description nodes
        - Deletes column stat relationships and orphaned stat nodes
        - Deletes column programmatic description relationships and orphaned nodes
        - Deletes the column node itself
        - Does NOT delete nodes that may have other relationships (badges, type_metadata, lineage, etc.)

        :param column_uri: Column URI (key in Neo4j, format: table_uri/column_name)
        :param published_tag: Published tag for audit trail
        """
        pass

    @abstractmethod
    def create_update_column(
            self,
            *,
            column_uri: str,
            column_name: Optional[str] = None,
            col_type: Optional[str] = None,
            sort_order: Optional[int] = None,
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        """
        Create or update a column's properties (name, type, sort_order).

        :param column_uri: Column URI (key in Neo4j, format: table_uri/column_name)
        :param column_name: Column name (optional, only used for creation if column doesn't exist)
        :param col_type: Column data type (optional, only updates if provided)
        :param sort_order: Column sort order (optional, only updates if provided)
        :param published_tag: Published tag for audit trail
        """
        pass

    @abstractmethod
    def create_lineage(
            self,
            *,
            upstream_resource_key: str,
            downstream_resource_key: str,
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        """
        Create bidirectional lineage relationships between any two resources.

        Creates:
        - downstream -> HAS_UPSTREAM -> upstream
        - upstream -> HAS_DOWNSTREAM -> downstream

        :param upstream_resource_key: Key of the upstream resource (any resource type)
        :param downstream_resource_key: Key of the downstream resource (any resource type)
        :param published_tag: Published tag for audit trail
        """
        pass

    @abstractmethod
    def delete_lineage(
            self,
            *,
            upstream_resource_key: str,
            downstream_resource_key: str,
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        """
        Delete bidirectional lineage relationships between any two resources.

        Deletes:
        - downstream -> HAS_UPSTREAM -> upstream
        - upstream -> HAS_DOWNSTREAM -> downstream

        :param upstream_resource_key: Key of the upstream resource (any resource type)
        :param downstream_resource_key: Key of the downstream resource (any resource type)
        :param published_tag: Published tag for audit trail
        """
        pass

    @abstractmethod
    def get_table_stats(self, *,
                        table_uri: str) -> List:
        pass

    @abstractmethod
    def create_update_table_stats(
            self,
            *,
            table_uri: str,
            stats: List[Stat],
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def delete_table_stats(self, *,
                           table_uri: str,
                           published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def create_update_custom_metadata(
            self,
            *,
            custom_metadata: CustomMetadata,
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> List[CustomMetadataNode]:
        pass

    @abstractmethod
    def get_custom_metadata(self, *,
                            label: str,
                            custom_metadata_uri: Optional[str] = None) -> Union[CustomMetadataNode,List[CustomMetadataNode]]:
        pass

    @abstractmethod
    def get_application(self, *,
                        application_uri: str) -> Application:
        pass

    @abstractmethod
    def create_update_application(
            self,
            *,
            application: Application,
            published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> Tuple[str, bool]:
        pass

    @abstractmethod
    def get_frequently_used_tables(self, *, user_email: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def add_resource_relation_by_user(self, *,
                                      id: str,
                                      user_id: str,
                                      relation_type: UserResourceRel,
                                      resource_type: ResourceType,
                                      published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def delete_resource_relation_by_user(self, *,
                                         id: str,
                                         user_id: str,
                                         relation_type: UserResourceRel,
                                         resource_type: ResourceType) -> None:
        pass

    @abstractmethod
    def get_dashboard(self,
                      dashboard_uri: str,
                      ) -> DashboardDetailEntity:
        pass

    @abstractmethod
    def get_dashboard_description(self, *,
                                  id: str) -> Description:
        pass

    @abstractmethod
    def put_dashboard_description(self, *,
                                  id: str,
                                  description: str,
                                  published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def get_resources_using_table(self, *,
                                  id: str,
                                  resource_type: ResourceType) -> Dict[str, List[DashboardSummary]]:
        pass

    @abstractmethod
    def get_lineage(self, *,
                    id: str, resource_type: ResourceType, direction: str, depth: int) -> Lineage:
        """
        Method should be implemented to obtain lineage from whatever source is preferred internally
        :param direction: if the request is for a list of upstream/downstream nodes or both
        :param depth: the level of lineage requested (ex: 1 would mean only nodes directly connected
        to the current id in whatever direction is specified)
        """
        pass

    @abstractmethod
    def get_feature(self, *, feature_uri: str) -> Feature:
        pass

    @abstractmethod
    def get_resource_description(self, *,
                                 resource_type: ResourceType,
                                 uri: str) -> Description:
        pass

    @abstractmethod
    def put_resource_description(self, *,
                                 resource_type: ResourceType,
                                 uri: str,
                                 description: str,
                                 published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def add_resource_owner(self, *,
                           uri: str,
                           resource_type: ResourceType,
                           owner: str,
                           published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def delete_resource_owner(self, *,
                              uri: str,
                              resource_type: ResourceType,
                              owner: str) -> None:
        pass

    @abstractmethod
    def get_resource_generation_code(self, *,
                                     uri: str,
                                     resource_type: ResourceType) -> GenerationCode:
        pass

    @abstractmethod
    def get_snowflake_table_shares(self, *, table_uri: str) -> Union[List[SnowflakeTableShare], None]:
        pass

    @abstractmethod
    def get_data_provider(self, *, data_provider_uri: str) -> DataProvider:
        pass

    @abstractmethod
    def get_file(self, *, file_uri: str) -> File:
        pass

    @abstractmethod
    def get_file_description(self, *,
                             id: str) -> Union[str, None]:
        pass

    @abstractmethod
    def put_file_description(self, *,
                             id: str,
                             description: str,
                             published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def put_data_provider_description(self, *,
                                      id: str,
                                      description: str,
                                      published_tag: str = DEFAULT_EDITED_PUBLISHED_TAG) -> None:
        pass

    @abstractmethod
    def get_database(self, *, id: str = None) -> Union[Database, None]:
        pass

    @abstractmethod
    def get_databases(self) -> List[Database]:
        pass

    @abstractmethod
    def get_cluster(self, *, id: Optional[str] = None, database: Optional[str] = None, cluster: Optional[str] = None) -> Union[Cluster, None]:
        pass

    @abstractmethod
    def get_clusters(self, *, database: Optional[str] = None) -> List[Cluster]:
        pass

    @abstractmethod
    def get_schema(self, *, id: Optional[str] = None, database: Optional[str] = None, cluster: Optional[str] = None, schema: Optional[str] = None) -> Union[Cluster, None]:
        pass

    @abstractmethod
    def get_schemas(self, *, database: Optional[str] = None, cluster: Optional[str] = None) -> List[Cluster]:
        pass