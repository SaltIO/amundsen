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
            SELECT
                {cluster_source} as cluster,
                st.schemaname as schema,
                st.relname as name,
                pgtd.description as description,
                att.attname as col_name,
                pgtyp.typname as col_type,
                pgcd.description as col_description,
                att.attnum as col_sort_order,
                CASE
                    WHEN pg_class.relkind = 'v' THEN true
                    ELSE false
                END AS is_view
            FROM pg_catalog.pg_attribute att
            INNER JOIN
                pg_catalog.pg_statio_all_tables as st
                on att.attrelid=st.relid
            INNER JOIN
                pg_catalog.pg_class pg_class
                ON st.relid = pg_class.oid
            LEFT JOIN
                pg_catalog.pg_type pgtyp
                on pgtyp.oid=att.atttypid
            LEFT JOIN
                pg_catalog.pg_description pgtd
                on pgtd.objoid=st.relid and pgtd.objsubid=0
            LEFT JOIN
              pg_catalog.pg_description pgcd
              on pgcd.objoid=st.relid and pgcd.objsubid=att.attnum
            WHERE att.attnum >=0 and {where_clause_suffix}
            ORDER by cluster, schema, name, col_sort_order;
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

    def get_view_def_sql_statement(self, schema_name, view_name) -> Any:
        return """
            SELECT
                view_definition
            FROM
                pg_views
            WHERE
                view_schema = '{schema_name}'
                AND view_name = '{view_name}';
        """.format(schema_name=schema_name, view_name=view_name)

    def get_scope(self) -> str:
        return 'extractor.postgres_metadata'
