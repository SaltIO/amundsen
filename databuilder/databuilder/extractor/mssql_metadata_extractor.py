# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from collections import namedtuple
from itertools import groupby
from typing import (
    Any, Dict, Iterator, Union,
)

from pyhocon import ConfigFactory, ConfigTree

from sqlalchemy import create_engine
from sqlglot import parse_one, exp

from databuilder import Scoped
from databuilder.extractor import sql_alchemy_extractor
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata
from databuilder.models.table_lineage import TableLineage

TableKey = namedtuple('TableKey', ['schema_name', 'table_name'])

LOGGER = logging.getLogger(__name__)


class MSSQLMetadataExtractor(Extractor):
    """
    Extracts Microsoft SQL Server table and column metadata from underlying
    meta store database using SQLAlchemyExtractor
    """

    # SELECT statement from MS SQL to extract table and column metadata
    SQL_STATEMENT = """
        SELECT DISTINCT
            {cluster_source} AS cluster,
            TBL.TABLE_SCHEMA AS [schema_name],
            TBL.TABLE_NAME AS [name],
            CAST(PROP.VALUE AS NVARCHAR(MAX)) AS [description],
            COL.COLUMN_NAME AS [col_name],
            COL.DATA_TYPE AS [col_type],
            CAST(PROP_COL.VALUE AS NVARCHAR(MAX)) AS [col_description],
            COL.ORDINAL_POSITION AS col_sort_order,
            CASE WHEN TBL.TABLE_TYPE = 'VIEW' THEN 'True' ELSE 'False' END AS is_view
        FROM INFORMATION_SCHEMA.TABLES TBL
        INNER JOIN INFORMATION_SCHEMA.COLUMNS COL
            ON (COL.TABLE_NAME = TBL.TABLE_NAME
                AND COL.TABLE_SCHEMA = TBL.TABLE_SCHEMA )
        LEFT JOIN SYS.EXTENDED_PROPERTIES PROP
            ON (PROP.MAJOR_ID = OBJECT_ID(TBL.TABLE_SCHEMA + '.' + TBL.TABLE_NAME)
                AND PROP.MINOR_ID = 0
                AND PROP.NAME = 'MS_Description')
        LEFT JOIN SYS.EXTENDED_PROPERTIES PROP_COL
            ON (PROP_COL.MAJOR_ID = OBJECT_ID(TBL.TABLE_SCHEMA + '.' + TBL.TABLE_NAME)
                AND PROP_COL.MINOR_ID = COL.ORDINAL_POSITION
                AND PROP_COL.NAME = 'MS_Description')
        WHERE (TBL.TABLE_TYPE = 'base table' OR TBL.TABLE_TYPE = 'VIEW') {where_clause_suffix}
        ORDER BY
            CLUSTER,
            SCHEMA_NAME,
            NAME,
            COL_SORT_ORDER;
    """

    # CONFIG KEYS
    WHERE_CLAUSE_SUFFIX_KEY = 'where_clause_suffix'
    CLUSTER_KEY = 'cluster_key'
    USE_CATALOG_AS_CLUSTER_NAME = 'use_catalog_as_cluster_name'
    DATABASE_KEY = 'database_key'

    # Default values
    DEFAULT_CLUSTER_NAME = 'DB_NAME()'

    DEFAULT_CONFIG = ConfigFactory.from_dict({
        WHERE_CLAUSE_SUFFIX_KEY: '',
        CLUSTER_KEY: DEFAULT_CLUSTER_NAME,
        USE_CATALOG_AS_CLUSTER_NAME: True}
    )

    DEFAULT_WHERE_CLAUSE_VALUE = 'and tbl.table_schema in {schemas}'

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(MSSQLMetadataExtractor.DEFAULT_CONFIG)

        self._cluster = conf.get_string(MSSQLMetadataExtractor.CLUSTER_KEY)

        if conf.get_bool(MSSQLMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME):
            cluster_source = "DB_NAME()"
        else:
            cluster_source = f"'{self._cluster}'"

        self._database = conf.get_string(
            MSSQLMetadataExtractor.DATABASE_KEY,
            default='mssql')

        config_where_clause = conf.get_string(
            MSSQLMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY)

        LOGGER.info("Crawling for Schemas %s", config_where_clause)

        if config_where_clause:
            where_clause_suffix = MSSQLMetadataExtractor \
                .DEFAULT_WHERE_CLAUSE_VALUE \
                .format(schemas=config_where_clause)
        else:
            where_clause_suffix = ''

        self.sql_stmt = MSSQLMetadataExtractor.SQL_STATEMENT.format(
            where_clause_suffix=where_clause_suffix,
            cluster_source=cluster_source
        )

        LOGGER.info('SQL for MS SQL Metadata: %s', self.sql_stmt)

        self._alchemy_extractor = sql_alchemy_extractor.from_surrounding_config(conf, self.sql_stmt)
        sql_alch_conf = Scoped.get_scoped_conf(conf, self._alchemy_extractor.get_scope())
        self.connection = self._get_connection(sql_alch_conf)

        self._extract_iter: Union[None, Iterator] = None

    def _get_connection(self, sql_alch_conf) -> Any:
        """
        Create a SQLAlchemy connection to Database
        """
        conn_string = sql_alch_conf.get_string(SQLAlchemyExtractor.CONN_STRING)

        connect_args = {
            k: v
            for k, v in sql_alch_conf.get_config(
                'connect_args', default=ConfigTree()
            ).items()
        }
        engine = create_engine(conn_string, connect_args=connect_args)
        conn = engine.connect()
        return conn

    def get_key_sql_statement(self, schema_name, table_name) -> Any:
        return """
            SELECT
                CASE
                    WHEN CONSTRAINT_TYPE = 'PRIMARY KEY' THEN 'Primary Key'
                    WHEN CONSTRAINT_TYPE = 'FOREIGN KEY' THEN 'Foreign Key'
                    WHEN CONSTRAINT_TYPE = 'UNIQUE' THEN 'Unique Constraint'
                    ELSE 'Unknown'
                END AS constraint_type,
                SCHEMA_NAME(t.schema_id) AS table_schema,
                t.name AS table_name,
                c.name AS column_name
            FROM sys.tables t
            INNER JOIN sys.columns c ON t.object_id = c.object_id
            LEFT JOIN (
                SELECT
                    KCU.TABLE_SCHEMA,
                    KCU.TABLE_NAME,
                    KCU.COLUMN_NAME,
                    TC.CONSTRAINT_TYPE
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS TC
                JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE KCU
                    ON TC.CONSTRAINT_NAME = KCU.CONSTRAINT_NAME
                    AND TC.TABLE_NAME = KCU.TABLE_NAME
                WHERE TC.CONSTRAINT_TYPE IN ('PRIMARY KEY', 'FOREIGN KEY', 'UNIQUE')
            ) AS cons ON t.name = cons.TABLE_NAME AND c.name = cons.COLUMN_NAME
            WHERE SCHEMA_NAME(t.schema_id) = '{schema_name}'
            AND t.name = '{table_name}'
            ORDER BY table_schema, table_name, column_name;
        """.format(schema_name=schema_name, table_name=table_name)

    def get_view_def_sql_statement(self, schema_name, table_name) -> Any:
        return """
            SELECT OBJECT_SCHEMA_NAME(object_id) AS schema_name,
                OBJECT_NAME(object_id) AS view_name,
                definition AS view_definition
            FROM sys.sql_modules
            WHERE OBJECTPROPERTY(object_id, 'IsView') = 1
                AND OBJECT_SCHEMA_NAME(object_id) = '{schema_name}'
                AND OBJECT_NAME(object_id) = '{table_name}';
        """.format(schema_name=schema_name, table_name=table_name)

    def close(self) -> None:
        if getattr(self, '_alchemy_extractor', None) is not None:
            self._alchemy_extractor.close()

    def extract(self) -> Union[TableMetadata, None]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return 'extractor.mssql_metadata'

    def _get_extract_iter(self) -> Iterator[TableMetadata]:
        """
        Using itertools.groupby and raw level iterator,
        it groups to table and yields TableMetadata
        :return:
        """
        for key, group in groupby(self._get_raw_extract_iter(), self._get_table_key):
            columns = []
            key_cols = None

            for row in group:
                last_row = row

                if key_cols is None:
                    results = self.connection.execute(self.get_key_sql_statement(schema_name=last_row['schema_name'], table_name=last_row['name']))
                    LOGGER.info(f"results={results}")
                    if results:
                        key_cols = {}
                        for key_row in results:
                            # Access columns by name or index
                            constraint_type = key_row['constraint_type'].lower().replace(" ", "")
                            key_column = key_row['column_name']

                            if key_column in key_cols:
                                key_cols[key_column].append(constraint_type)
                            else:
                                key_cols[key_column] = [constraint_type]

                col_badges = []
                if key_cols is not None and row['col_name'] in key_cols:
                    LOGGER.info(f"Found KEY={row['col_name']}")
                    LOGGER.info(f"Badges={key_cols[row['col_name']]}")
                    col_badges = key_cols[row['col_name']]

                col_metadata = ColumnMetadata(row['col_name'], row['col_description'],
                                              row['col_type'], row['col_sort_order'],
                                              badges=col_badges)

                columns.append(col_metadata)

            table_metadata = TableMetadata(
                self._database,
                last_row['cluster'],
                last_row['schema_name'],
                last_row['name'],
                last_row['description'],
                columns,
                tags=last_row['schema_name'],
                is_view=last_row['is_view'])
            yield table_metadata

            if bool(last_row['is_view']) == True:
                results = None
                try:
                    results = self.connection.execute(self.get_view_def_sql_statement(schema_name=last_row['schema_name'], view_name=last_row['name']))
                except Exception as e:
                    LOGGER.exception('Failed to get view def:')
                finally:
                    if results is not None:
                        view_row = results.fetchone()
                        LOGGER.info(f"view_row={view_row}")
                        if view_row:
                            view_def = view_row[0]
                            if view_def:
                                try:
                                    view_def = view_def.replace(']', '').replace('[', '')
                                    view_tables = parse_one(view_def).find_all(exp.Table)

                                    LOGGER.info(f"View table: {view_tables}")

                                    if view_tables is not None and len(view_tables) > 0:
                                        for table in view_tables:
                                            table_key = TableMetadata.TABLE_KEY_FORMAT.format(db=self._database, cluster=last_row['cluster'], schema=table.db.lower(), tbl=table.this.lower())
                                            LOGGER.info(f"Table Lineage: table={table_key}   downstream={table_metadata._get_table_key()}")
                                            yield TableLineage(
                                                table_key=table_key,
                                                downstream_deps=[table_metadata._get_table_key()]
                                            )

                                except Exception as e:
                                    LOGGER.exception(f"Error parsing the view def for {last_row['schema_name']}.{last_row['name']}:")

    def _get_raw_extract_iter(self) -> Iterator[Dict[str, Any]]:
        """
        Provides iterator of result row from SQLAlchemy extractor
        :return:
        """
        row = self._alchemy_extractor.extract()
        while row:
            yield row
            row = self._alchemy_extractor.extract()

    def _get_table_key(self, row: Dict[str, Any]) -> Union[TableKey, None]:
        """
        Table key consists of schema and table name
        :param row:
        :return:
        """
        if row:
            return TableKey(
                schema_name=row['schema_name'],
                table_name=row['name'])

        return None
