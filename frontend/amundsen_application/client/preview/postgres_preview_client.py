
import logging
import os
from typing import Dict,Tuple,Any,List  # noqa: F401
import json
from urllib.parse import quote

from amundsen_application.client.preview.sqlalchemy_base_preview_client import SqlAlchemyBasePreviewClient

class PostgresPreviewClient(SqlAlchemyBasePreviewClient):

    SQL_STATEMENT = 'SELECT * FROM {schema}.{table} LIMIT {limit};'
    CONN_STR = 'postgresql://{user}:{password}@{host}:{port}/{database}'

    logging.basicConfig()
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    def __init__(self, host: str = None, port: int = None, username: str = None, password: str = None, databases: List[str] = None, conn_args: Dict[Any,Any] = None) -> None:

        super().__init__()

        self.host = (host if host is not None else os.getenv("PREVIEW_CLIENT_POSTGRES_HOST"))
        self.port = (port if port is not None else os.getenv("PREVIEW_CLIENT_POSTGRES_PORT", "5432"))
        self.username = (username if username is not None else os.getenv("PREVIEW_CLIENT_POSTGRES_USERNAME"))
        self.password = (password if password is not None else os.getenv("PREVIEW_CLIENT_POSTGRES_PASSWORD"))
        self.conn_args = (conn_args if conn_args is not None else os.getenv("PREVIEW_CLIENT_POSTGRES_CONN_ARGS"))
        self.databases = (databases if databases is not None else os.getenv("PREVIEW_CLIENT_POSTGRES_DATABASE"))
        if self.databases is not None:
            self.databases = (db.lower() for db in self.databases)
            self.databases = list(self.databases)

        if self.conn_args is None or self.conn_args == '':
            self.conn_args = {}
        if self.conn_args:
            self.conn_args = json.loads(self.conn_args)

        logging.info(f"host={self.host}")
        logging.info(f"port={self.port}")
        logging.info(f"username={self.username}")
        logging.info(f"conn_args={self.conn_args}")
        logging.info(f"databases={self.databases}")

    def _is_preview_client_configured(self) -> bool:
        return (self.host is not None and \
                self.port is not None and \
                self.username is not None and \
                self.password is not None)

    def is_supported_preview_source(self, params: Dict, optionalHeaders: Dict = None) -> bool:
        warehouse_type = params.get('database')
        cluster = params.get('cluster')

        # must be a postgres DB and if the cluster and database match
        if (warehouse_type is not None and warehouse_type.lower() == 'postgres') and \
           (self.databases is None or len(self.databases) == 0 or cluster is None or cluster.lower() in self.databases):

            if self._is_preview_client_configured():
                return True
            else:
                logging.warn('Table preview supported for source Postgres, but the PostgresPreviewClient was not setup correctly')
                return False
        else:
            logging.info(f'Skipping Postgres table preview for non-Postgres ({warehouse_type} and {cluster}) table')
            return False

    def get_sql(self, params: Dict, optionalHeaders: Dict = None) -> str:
        schema = params['schema']
        table = params['tableName']

        sql = PostgresPreviewClient.SQL_STATEMENT.format(schema=schema,
                                                         table=table,
                                                         limit=self.limit)

        return sql

    def get_conn_str(self, params: Dict, optionalHeaders: Dict = None)  -> Tuple[str,Dict[str,Any]]:
        database = params['cluster']

        conn_str = PostgresPreviewClient.CONN_STR.format(
            user=self.username,
            password=quote(self.password),
            host=self.host,
            port=self.port,
            database=database
        )

        return (conn_str,self.conn_args)
