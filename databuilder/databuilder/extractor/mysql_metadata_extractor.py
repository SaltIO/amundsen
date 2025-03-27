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

from queryparser.mysql import MySQLQueryProcessor
from queryparser.exceptions import QuerySyntaxError
import re

from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata
from databuilder.models.table_lineage import TableLineage

TableKey = namedtuple('TableKey', ['schema', 'table_name'])

LOGGER = logging.getLogger(__name__)


class MysqlMetadataExtractor(Extractor):
    """
    Extracts mysql table and column metadata from underlying meta store database using SQLAlchemyExtractor
    """
    # SELECT statement from mysql information_schema to extract table and column metadata
    SQL_STATEMENT = """
        SELECT
        lower(c.column_name) AS col_name,
        c.column_comment AS col_description,
        lower(c.data_type) AS col_type,
        lower(c.ordinal_position) AS col_sort_order,
        {cluster_source} AS cluster,
        lower(c.table_schema) AS "schema",
        lower(c.table_name) AS name,
        t.table_comment AS description,
        case when lower(t.table_type) = "view" then "true" else "false" end AS is_view
        FROM
        INFORMATION_SCHEMA.COLUMNS AS c
        LEFT JOIN
        INFORMATION_SCHEMA.TABLES t
            ON c.TABLE_NAME = t.TABLE_NAME
            AND c.TABLE_SCHEMA = t.TABLE_SCHEMA
        {where_clause_suffix}
        ORDER by cluster, "schema", name, col_sort_order ;
    """

    # PK_SQL_STATEMENT = """
    #     SELECT table_schema, table_name, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS primary_key_columns
    #     FROM INFORMATION_SCHEMA.STATISTICS
    #     WHERE INDEX_NAME = 'PRIMARY' and table_schema = '{schema_name}' and table_name = '{table_name}'
    #     GROUP BY TABLE_NAME;
    # """
    KEY_SQL_STATMENT = """
         SELECT
            tc.constraint_type,
            tc.table_schema,
            tc.table_name,
            kcu.column_name
        FROM
            information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.constraint_schema = kcu.constraint_schema
        WHERE
            tc.constraint_type in ('UNIQUE', 'PRIMARY KEY', 'FOREIGN KEY')
            AND tc.TABLE_SCHEMA = '{schema_name}'
            AND tc.TABLE_NAME = '{table_name}'
        GROUP BY tc.table_schema, tc.table_name, kcu.column_name, tc.constraint_type;
    """

    VIEW_SQL_STATEMENT = """
        SELECT
            VIEW_DEFINITION
        FROM
            information_schema.VIEWS
        WHERE
            TABLE_SCHEMA = '{schema_name}'
            AND TABLE_NAME = '{table_name}';
    """

    # CONFIG KEYS
    WHERE_CLAUSE_SUFFIX_KEY = 'where_clause_suffix'
    CLUSTER_KEY = 'cluster_key'
    USE_CATALOG_AS_CLUSTER_NAME = 'use_catalog_as_cluster_name'
    DATABASE_KEY = 'database_key'

    # Default values
    DEFAULT_CLUSTER_NAME = 'master'

    DEFAULT_CONFIG = ConfigFactory.from_dict(
        {WHERE_CLAUSE_SUFFIX_KEY: ' ', CLUSTER_KEY: DEFAULT_CLUSTER_NAME, USE_CATALOG_AS_CLUSTER_NAME: True}
    )

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(MysqlMetadataExtractor.DEFAULT_CONFIG)
        self._cluster = conf.get_string(MysqlMetadataExtractor.CLUSTER_KEY)

        if conf.get_bool(MysqlMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME):
            cluster_source = "c.table_catalog"
        else:
            cluster_source = f"'{self._cluster}'"

        self._database = conf.get_string(MysqlMetadataExtractor.DATABASE_KEY, default='mysql')

        self.sql_stmt = MysqlMetadataExtractor.SQL_STATEMENT.format(
            where_clause_suffix=conf.get_string(MysqlMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY),
            cluster_source=cluster_source
        )

        self._alchemy_extractor = SQLAlchemyExtractor()
        sql_alch_conf = Scoped.get_scoped_conf(conf, self._alchemy_extractor.get_scope()) \
            .with_fallback(ConfigFactory.from_dict({SQLAlchemyExtractor.EXTRACT_SQL: self.sql_stmt}))

        self.sql_stmt = sql_alch_conf.get_string(SQLAlchemyExtractor.EXTRACT_SQL)

        LOGGER.info('SQL for mysql metadata: %s', self.sql_stmt)

        self.connection = self._get_connection(sql_alch_conf)

        self._alchemy_extractor.init(sql_alch_conf)
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

    def extract(self) -> Union[TableMetadata, None]:
        if not self._extract_iter:
            self._extract_iter = self._get_extract_iter()
        try:
            return next(self._extract_iter)
        except StopIteration:
            return None

    def get_scope(self) -> str:
        return 'extractor.mysql_metadata'

    def _get_extract_iter(self) -> Iterator[TableMetadata]:
        """
        Using itertools.groupby and raw level iterator, it groups to table and yields TableMetadata
        :return:
        """
        for key, group in groupby(self._get_raw_extract_iter(), self._get_table_key):
            columns = []
            key_cols = None

            for row in group:
                last_row = row

                if key_cols is None:
                    results = self.connection.execute(MysqlMetadataExtractor.KEY_SQL_STATMENT.format(schema_name=last_row['schema'], table_name=last_row['name']))
                    # LOGGER.info(f"results={results}")
                    if results:
                        key_cols = {}
                        for key_row in results:
                            LOGGER.info(f"key_row={key_row}")
                            # Access columns by name or index
                            constraint_type = key_row['CONSTRAINT_TYPE'].lower().replace(" ", "")
                            key_column = key_row['COLUMN_NAME']

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

            table_metadata = TableMetadata(self._database,
                                           last_row['cluster'],
                                           last_row['schema'],
                                           last_row['name'],
                                           last_row['description'],
                                           columns,
                                           is_view=last_row['is_view'])
            yield table_metadata

            if bool(last_row['is_view']) == True:
                results = self.connection.execute(MysqlMetadataExtractor.VIEW_SQL_STATEMENT.format(schema_name=last_row['schema'], table_name=last_row['name']))
                view_row = results.fetchone()
                LOGGER.info(f"view_row={view_row}")
                if view_row:
                    view_def = view_row[0]
                    if view_def:
                        qp = MySQLQueryProcessor()
                        try:
                            view_def = MysqlMetadataExtractor.clean_view_def(view_def)
                            qp.set_query(view_def)

                            qp.process_query()

                            LOGGER.info(f"View table: {qp.tables}")

                            if qp.tables is not None and len(qp.tables) > 0:
                                for table in qp.tables:
                                    table_key = TableMetadata.TABLE_KEY_FORMAT.format(db=self._database, cluster=last_row['cluster'], schema=table[0].lower(), tbl=table[1].lower())
                                    LOGGER.info(f"Table Lineage: table={table_key}   downstream={table_metadata._get_table_key()}")
                                    yield TableLineage(
                                        table_key=table_key,
                                        downstream_deps=[table_metadata._get_table_key()]
                                    )

                        except QuerySyntaxError as e:
                            LOGGER.exception(f"Error parsing the query for {last_row['schema']}.{last_row['name']}:")

    def clean_view_def(view_def:str) -> str:
        # Regular expression pattern to match " - interval X day"
        pattern = r" [+-] interval \d+ day"
        # Replace all matches with an empty string
        cleaned_sql = re.sub(pattern, '', view_def).replace('coalesce', '').replace('collate', '').replace('utf8_general_ci', '')

        return cleaned_sql

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
            return TableKey(schema=row['schema'], table_name=row['name'])

        return None
