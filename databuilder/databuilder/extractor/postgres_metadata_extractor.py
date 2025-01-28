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
                    {cluster_source} AS cluster,
                    n.nspname AS schema,
                    c.relname AS name,
                    CASE
                        WHEN c.relkind IN ('v', 'm') THEN pg_get_viewdef(format('%I.%I', n.nspname, c.relname), true)
                        ELSE NULL
                    END AS view_definition,
                    c.relkind IN ('v', 'm') AS is_view,
                    c.relkind IN ('m') AS is_mat_view
                FROM pg_catalog.pg_class c
                INNER JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
                LEFT JOIN pg_inherits i ON c.oid = i.inhrelid  -- Join with pg_inherits to check for child partitions
                WHERE c.relkind IN ('r', 'v', 'm', 'p') AND i.inhrelid IS NULL {where_clause_suffix} -- Exclude child partitions
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
                WHERE c.relkind IN ('r', 'v', 'm', 'p') AND a.attnum > 0 {where_clause_suffix}
            ),
            Final AS (
                SELECT
                    o.cluster,
                    o.schema,
                    o.name,
                    c.col_name,
                    c.col_type,
                    c.col_description,
                    c.col_sort_order,
                    o.is_view,
                    o.is_mat_view,
                    o.view_definition
                FROM Objects o
                LEFT JOIN Columns c ON o.schema = c.schema AND o.name = c.name
                ORDER BY o.cluster, o.schema, o.name, c.col_sort_order
            )
            SELECT
                *
            FROM
                Final f
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
