# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import (  # noqa: F401
    Any, Dict, Iterator, Union,
)

from pyhocon import ConfigFactory, ConfigTree  # noqa: F401

from databuilder.extractor.base_postgres_metadata_extractor import BasePostgresMetadataExtractor


class PostgresMetadataExtractor(BasePostgresMetadataExtractor):
    """
    Extracts Postgres table and column metadata from underlying meta store database using SQLAlchemyExtractor
    """

    def get_sql_statement(self, use_catalog_as_cluster_name: bool, where_clause_suffix: str) -> str:
        if use_catalog_as_cluster_name:
            cluster_source = "current_database()"
        else:
            cluster_source = f"'{self._cluster}'"

        return """
            WITH Objects AS (
                SELECT
                    current_database() AS cluster,
                    n.nspname AS schema,
                    c.relname AS name,
                    CASE WHEN c.relkind = 'r' THEN NULL ELSE v.definition END AS object_description,
                    c.relkind = 'v' AS is_view
                FROM pg_catalog.pg_class c
                LEFT JOIN pg_catalog.pg_views v ON c.relname = v.viewname
                INNER JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                WHERE c.relkind IN ('r', 'v') {where_clause_suffix}
            ),
            Columns AS (
                SELECT
                    current_database() AS cluster,
                    n.nspname AS schema,
                    c.relname AS name,
                    a.attname AS col_name,
                    format_type(a.atttypid, a.atttypmod) AS col_type,
                    pd.description AS col_description,
                    a.attnum AS col_sort_order
                FROM pg_catalog.pg_attribute a
                INNER JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
                INNER JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                LEFT JOIN pg_catalog.pg_description pd ON c.oid = pd.objoid AND a.attnum = pd.objsubid
                WHERE c.relkind IN ('r', 'v') {where_clause_suffix} AND a.attnum > 0
            )
            SELECT
                o.cluster,
                o.schema,
                o.name,
                o.object_description,
                c.col_name,
                c.col_type,
                c.col_description,
                c.col_sort_order,
                o.is_view
            FROM Objects o
            LEFT JOIN Columns c ON o.schema = c.schema AND o.name = c.name
            ORDER BY o.cluster, o.schema, o.name, c.col_sort_order;
        """.format(
            cluster_source=cluster_source,
            where_clause_suffix=where_clause_suffix,
        )

    def get_key_sql_statement(self, schema_name, table_name) -> Any:
        return """
            SELECT
                CASE
                    WHEN con.contype = 'u' THEN 'UNIQUE'
                    WHEN con.contype = 'p' THEN 'PRIMARY KEY'
                    WHEN con.contype = 'f' THEN 'FOREIGN KEY'
                    ELSE 'OTHER'
                END AS constraint_type,
                ns.nspname AS table_schema,
                tbl.relname AS table_name,
                col.attname AS column_name
            FROM
                pg_constraint con
            JOIN
                pg_namespace ns ON ns.oid = con.connamespace
            JOIN
                pg_class tbl ON tbl.oid = con.conrelid
            JOIN
                pg_attribute col ON col.attrelid = con.conrelid
                AND col.attnum = ANY(con.conkey)
            WHERE
                con.contype IN ('u', 'p', 'f') -- Unique, Primary Key, Foreign Key
                AND ns.nspname = '{schema_name}'
                AND tbl.relname = '{table_name}';
        """.format(schema_name=schema_name, table_name=table_name)

    def get_old_view_def_sql_statement(self, schema_name, view_name) -> Any:
        return """
            SELECT
                view_definition
            FROM
                pg_views
            WHERE
                view_schema = '{schema_name}'
                AND view_name = '{view_name}';
        """.format(schema_name=schema_name, view_name=view_name)

    def get_new_view_def_sql_statement(self, schema_name, view_name) -> Any:
        return """
            SELECT
                definition
            FROM
                pg_views
            WHERE
                schemaname = '{schema_name}'
                AND viewname = '{view_name}';
        """.format(schema_name=schema_name, view_name=view_name)

    def get_scope(self) -> str:
        return 'extractor.postgres_metadata'
