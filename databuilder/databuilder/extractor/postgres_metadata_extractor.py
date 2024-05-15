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
                att.attnum as col_sort_order
            FROM pg_catalog.pg_attribute att
            INNER JOIN
                pg_catalog.pg_statio_all_tables as st
                on att.attrelid=st.relid
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

    def get_primary_key_sql_statement(self, schema_name, table_name) -> Any:
        return """
            SELECT tc.table_schema, tc.table_name, array_agg(kcu.column_name ORDER BY kcu.ordinal_position) AS primary_key_columns
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.constraint_schema = kcu.constraint_schema
            WHERE tc.constraint_type = 'PRIMARY KEY'
            AND tc.table_schema = '{schema_name}'
            AND tc.table_name '{table_name}'
            GROUP BY tc.table_schema, tc.table_name;
        """.format(schema_name=schema_name, table_name=table_name)

    def get_scope(self) -> str:
        return 'extractor.postgres_metadata'
