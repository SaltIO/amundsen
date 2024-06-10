# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
import logging
from collections import namedtuple
from itertools import groupby
from typing import (
    Any, Dict, Iterator, Union,
)

from pyhocon import ConfigFactory, ConfigTree
from sqlalchemy import create_engine

from queryparser.postgresql import PostgreSQLQueryProcessor
from queryparser.exceptions import QuerySyntaxError


from databuilder import Scoped
from databuilder.extractor.base_extractor import Extractor
from databuilder.extractor.sql_alchemy_extractor import SQLAlchemyExtractor
from databuilder.models.table_metadata import ColumnMetadata, TableMetadata
from databuilder.models.table_lineage import TableLineage

TableKey = namedtuple('TableKey', ['schema', 'table_name'])

LOGGER = logging.getLogger(__name__)


class BasePostgresMetadataExtractor(Extractor):
    """
    Extracts Postgres table and column metadata from underlying meta store database using SQLAlchemyExtractor
    """

    # CONFIG KEYS
    WHERE_CLAUSE_SUFFIX_KEY = 'where_clause_suffix'
    CLUSTER_KEY = 'cluster_key'
    USE_CATALOG_AS_CLUSTER_NAME = 'use_catalog_as_cluster_name'
    DATABASE_KEY = 'database_key'

    # Default values
    DEFAULT_CLUSTER_NAME = 'master'

    DEFAULT_CONFIG = ConfigFactory.from_dict(
        {WHERE_CLAUSE_SUFFIX_KEY: 'true', CLUSTER_KEY: DEFAULT_CLUSTER_NAME, USE_CATALOG_AS_CLUSTER_NAME: True}
    )

    @abc.abstractmethod
    def get_sql_statement(self, use_catalog_as_cluster_name: bool, where_clause_suffix: str) -> Any:
        """
        :return: Provides a record or None if no more to extract
        """
        return None

    @abc.abstractmethod
    def get_key_sql_statement(self, schema_name, table_name) -> Any:
        return None

    @abc.abstractmethod
    def get_old_view_def_sql_statement(self, schema_name, table_name) -> Any:
        return None

    @abc.abstractmethod
    def get_new_view_def_sql_statement(self, schema_name, view_name) -> Any:
        return None

    def init(self, conf: ConfigTree) -> None:
        conf = conf.with_fallback(BasePostgresMetadataExtractor.DEFAULT_CONFIG)
        self._cluster = conf.get_string(BasePostgresMetadataExtractor.CLUSTER_KEY)

        self._database = conf.get_string(BasePostgresMetadataExtractor.DATABASE_KEY, default='postgres')

        # where_clause_suffix = conf.get_string(BasePostgresMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY)
        # if where_clause_suffix and where_clause_suffix != '':
        #     where_clause_suffix = f'WHERE {where_clause_suffix}'

        self.sql_stmt = self.get_sql_statement(
            use_catalog_as_cluster_name=conf.get_bool(BasePostgresMetadataExtractor.USE_CATALOG_AS_CLUSTER_NAME),
            where_clause_suffix=conf.get_string(BasePostgresMetadataExtractor.WHERE_CLAUSE_SUFFIX_KEY),
        )

        self._alchemy_extractor = SQLAlchemyExtractor()
        sql_alch_conf = Scoped.get_scoped_conf(conf, self._alchemy_extractor.get_scope())\
            .with_fallback(ConfigFactory.from_dict({SQLAlchemyExtractor.EXTRACT_SQL: self.sql_stmt}))

        self.sql_stmt = sql_alch_conf.get_string(SQLAlchemyExtractor.EXTRACT_SQL)

        LOGGER.info('SQL for postgres metadata: %s', self.sql_stmt)

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
                    results = self.connection.execute(self.get_key_sql_statement(schema_name=last_row['schema'], table_name=last_row['name']))
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

            table_metadata = TableMetadata(self._database, last_row['cluster'],
                                           last_row['schema'],
                                           last_row['name'],
                                           last_row['description'] if 'description' in last_row else None,
                                           columns,
                                           is_view=last_row['is_view'])
            yield table_metadata

            if bool(last_row['is_view']) == True:
                results = None
                try:
                    results = self.connection.execute(self.get_new_view_def_sql_statement(schema_name=last_row['schema'], view_name=last_row['name']))
                except Exception as e:
                    results = self.connection.execute(self.get_old_view_def_sql_statement(schema_name=last_row['schema'], view_name=last_row['name']))
                finally:
                    if results is not None:
                        view_row = results.fetchone()
                        LOGGER.info(f"view_row={view_row}")
                        if view_row:
                            view_def = view_row[0]
                            if view_def:
                                qp = PostgreSQLQueryProcessor()
                                try:
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
