# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import textwrap
from typing import Any

from databuilder.extractor.neo4j_search_data_extractor import Neo4jSearchDataExtractor
from pyhocon import ConfigTree

from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.neo4j_extractor import Neo4jExtractor
from databuilder.publisher.neo4j_csv_publisher import JOB_PUBLISH_TAG


class Neo4jSearchEmbeddingDataExtractor(Neo4jSearchDataExtractor):
    """
    Extractor to fetch data required to support search from Neo4j graph database
    Use Neo4jExtractor extractor class
    """

    DEFAULT_NEO4J_TABLE_EMBEDDING_CYPHER_QUERY = textwrap.dedent(
        """
        MATCH (db:Database)-[:CLUSTER]->(cluster:Cluster)-[:SCHEMA]->(schema:Schema)-[:TABLE]->(table:Table)
        {publish_tag_filter}
        OPTIONAL MATCH (table)-[:DESCRIPTION]->(table_description:Description)
        OPTIONAL MATCH (table)-[:DESCRIPTION]->(prog_descs:Programmatic_Description)
        WITH db, cluster, schema, table, table_description,
        COLLECT(prog_descs.description) as programmatic_descriptions
        OPTIONAL MATCH (table)-[:TAGGED_BY]->(tags:Tag)
        WITH db, cluster, schema, table, table_description, programmatic_descriptions,
        COLLECT(DISTINCT tags.key) as tags
        OPTIONAL MATCH (table)-[:HAS_BADGE]->(badges:Badge)
        WITH db, cluster, schema, table, table_description, programmatic_descriptions, tags,
        COLLECT(DISTINCT badges.key) as badges
        WITH db, cluster, schema, table, table_description, programmatic_descriptions, tags, badges
        WITH db, cluster, schema, table, table_description, tags, badges, programmatic_descriptions
        RETURN
            db.key as database_key,
            cluster.key as cluster_key,
            schema.key as schema_key,
            table.name AS name, table.key AS key,
            table_description.description AS description,
            tags,
            badges,
            programmatic_descriptions
        ORDER BY table.key;
        """
    )

    DEFAULT_NEO4J_COLUMN_EMBEDDING_CYPHER_QUERY = textwrap.dedent(
        """
        MATCH (db:Database)-[:CLUSTER]->(cluster:Cluster)-[:SCHEMA]->(schema:Schema)-[:TABLE]->(table:Table)-[:COLUMN]->(column:Column)
        {publish_tag_filter}
        OPTIONAL MATCH (column)-[:DESCRIPTION]->(column_description:Description)
        OPTIONAL MATCH (column)-[:TAGGED_BY]->(column_tags:Tag) WHERE column_tags.tag_type='default'
        WITH db, cluster, schema, column, column_description, table, COLLECT(DISTINCT toLower(column_tags.key)) as column_tags
        OPTIONAL MATCH (column)-[:HAS_BADGE]->(column_badges:Badge)
        WITH db, cluster, schema, column, column_description, column_tags, table, COLLECT(DISTINCT toLower(column_badges.key)) as column_badges
        OPTIONAL MATCH (table)-[:DESCRIPTION]->(table_description:Description)
        OPTIONAL MATCH (table)-[:TAGGED_BY]->(table_tags:Tag) WHERE table_tags.tag_type='default'
        WITH db, cluster, schema, column, column_description, column_tags, column_badges, table, table_description, COLLECT(DISTINCT toLower(table_tags.key)) as table_tags
        OPTIONAL MATCH (table)-[:HAS_BADGE]->(table_badges:Badge)
        WITH db, cluster, schema, column, column_description, column_tags, column_badges, table, table_description, table_tags, COLLECT(DISTINCT toLower(table_badges.key)) as table_badges
        RETURN
            column.key AS key,
            column.name AS name,
            column.col_type AS data_type,
            column_description.description AS description,
            column_tags as tags,
            column_badges as badges,
            table.name AS table_name,
            table.key AS table_key,
            table_description.description AS table_description,
            table_badges,
            table_tags,
            db.key as database_key,
            cluster.key as cluster_key,
            schema.key as schema_key
        ORDER BY
            column.key;
        """
    )

    DEFAULT_NEO4J_USER_EMBEDDING_CYPHER_QUERY = textwrap.dedent(
        """
        MATCH (user:User)
        OPTIONAL MATCH (user)-[read:READ]->(a)
        OPTIONAL MATCH (user)-[own:OWNER_OF]->(b)
        OPTIONAL MATCH (user)-[follow:FOLLOWED_BY]->(c)
        OPTIONAL MATCH (user)-[manage_by:MANAGE_BY]->(manager)
        {publish_tag_filter}
        with user, a, b, c, read, own, follow, manager
        where user.full_name is not null
        RETURN
            user.email as key,
            user.email as email,
            user.first_name as first_name,
            user.last_name as last_name,
            user.full_name as full_name,
            user.team_name as team_name,
            user.employee_type as employee_type,
            user.role_name as role_name
        order by user.email
        """
    )

    DEFAULT_NEO4J_DASHBOARD_EMBEDDING_CYPHER_QUERY = textwrap.dedent(
        """
         MATCH (dashboard:Dashboard)
         {publish_tag_filter}
         MATCH (dashboard)-[:DASHBOARD_OF]->(dbg:Dashboardgroup)
         MATCH (dbg)-[:DASHBOARD_GROUP_OF]->(cluster:Cluster)
         OPTIONAL MATCH (dashboard)-[:DESCRIPTION]->(db_descr:Description)
         OPTIONAL MATCH (dbg)-[:DESCRIPTION]->(dbg_descr:Description)
         OPTIONAL MATCH (dashboard)-[:EXECUTED]->(last_exec:Execution)
         WHERE split(last_exec.key, '/')[5] = '_last_successful_execution'
         OPTIONAL MATCH (dashboard)-[read:READ_BY]->(user:User)
         WITH dashboard, dbg, db_descr, dbg_descr, cluster, last_exec, SUM(read.read_count) AS total_usage
         OPTIONAL MATCH (dashboard)-[:HAS_QUERY]->(query:Query)-[:HAS_CHART]->(chart:Chart)
         WITH dashboard, dbg, db_descr, dbg_descr, cluster, last_exec, COLLECT(DISTINCT query.name) as query_names,
         COLLECT(DISTINCT chart.name) as chart_names,
         total_usage
         OPTIONAL MATCH (dashboard)-[:TAGGED_BY]->(tags:Tag) // WHERE tags.tag_type='default'
         WITH dashboard, dbg, db_descr, dbg_descr, cluster, last_exec, query_names, chart_names, total_usage,
         COLLECT(DISTINCT tags.key) as tags
         OPTIONAL MATCH (dashboard)-[:HAS_BADGE]->(badges:Badge)
         WITH  dashboard, dbg, db_descr, dbg_descr, cluster, last_exec, query_names, chart_names, total_usage, tags,
         COLLECT(DISTINCT badges.key) as badges
         RETURN
            dashboard.key as key,
            split(dashboard.key, '_')[0] as product,
            dbg.name as group_name,
            dashboard.name as name,
            cluster.name as cluster,
            coalesce(db_descr.description, '') as description,
            coalesce(dbg.description, '') as group_description,
            query_names,
            chart_names,
            tags,
            badges
         order by dbg.name
        """
    )

    DEFAULT_NEO4J_DATA_PROVIDER_EMBEDDING_CYPHER_QUERY = textwrap.dedent(
        """
        MATCH (dp:Data_Provider)
        OPTIONAL MATCH (dc:Data_Channel)-[:DATA_CHANNEL_OF]->(dp)
        OPTIONAL MATCH (dl:Data_Location)-[:DATA_LOCATION_OF]->(dc)
        OPTIONAL MATCH (dp)-[:DESCRIPTION]->(data_provider_desc:Description)
        OPTIONAL MATCH (dp)-[:TAGGED_BY]->(tags:Tag)
        {publish_tag_filter}
        WITH dp, data_provider_desc, COLLECT(DISTINCT tags.key) as tags, dc, dl
        RETURN
            dp.name as name,
            dp.key as key,
            data_provider_desc.description as description,
            tags
        """
    )

    DEFAULT_NEO4J_FILE_EMBEDDING_CYPHER_QUERY = textwrap.dedent(
        """
        MATCH (f:File)
        OPTIONAL MATCH (f)-[:FILE_OF]->(dl:Data_Location)
        OPTIONAL MATCH (f)-[:FILE_OF]->(dc:Data_Channel)-[:DATA_CHANNEL_OF]->(dp:Data_Provider)
        OPTIONAL MATCH (f)-[:DESCRIPTION]->(file_desc:Description)
        OPTIONAL MATCH (f)-[:TAGGED_BY]->(tags:Tag)
        {publish_tag_filter}
        WITH f, file_desc, COLLECT(DISTINCT tags.key) as tags, dl, dc, dp
        RETURN
            f.name as name,
            f.key as key,
            file_desc.description as description,
            f.type as type,
            f.category as category,
            f.path as path,
            dl.key as data_location_key,
            dc.key as data_channel_key,
            dp.key as data_provider_key,
            tags
        """
    )

    DEFAULT_EMBEDDING_QUERY_BY_ENTITY = {
        'table': DEFAULT_NEO4J_TABLE_EMBEDDING_CYPHER_QUERY,
        'column': DEFAULT_NEO4J_COLUMN_EMBEDDING_CYPHER_QUERY,
        'user': DEFAULT_NEO4J_USER_EMBEDDING_CYPHER_QUERY,
        'dashboard': DEFAULT_NEO4J_DASHBOARD_EMBEDDING_CYPHER_QUERY,
        'file': DEFAULT_NEO4J_FILE_EMBEDDING_CYPHER_QUERY,
        'data_provider': DEFAULT_NEO4J_DATA_PROVIDER_EMBEDDING_CYPHER_QUERY
    }

    def get_default_query(self, entity: str) -> str:
        return Neo4jSearchEmbeddingDataExtractor.DEFAULT_EMBEDDING_QUERY_BY_ENTITY[entity]
