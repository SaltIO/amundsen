from abc import abstractmethod
from http import HTTPStatus
import os
import logging
from typing import Dict, Tuple, Any, List  # noqa: F401

from sqlalchemy import create_engine, inspect

# from flask import Response, jsonify, make_response, current_app as app
from flask import Response, make_response, current_app as app
from marshmallow import ValidationError
import simplejson as json

from amundsen_application.models.preview_data import PreviewData, PreviewDataSchema, ColumnItem
from amundsen_application.client.preview.factory_base_preview_client import FactoryBasePreviewClient
from amundsen_application.client.preview.postgres_preview_client import PostgresPreviewClient

LOGGER = logging.getLogger(__name__)

# Consider a multi-database preview client
class PostgresFactoryPreviewClient(FactoryBasePreviewClient):


    def __init__(self,) -> None:
        self.pg_preview_clients: List[PostgresPreviewClient] = []

        for client in os.getenv("PREVIEW_CLIENT_POSTGRES_FACTORY_CLIENTS", '').split(","):
            host = os.getenv(f"{client}_HOST")
            port = os.getenv(f"{client}_PORT", "5432")
            username = os.getenv(f"{client}_USERNAME")
            password = os.getenv(f"{client}_PASSWORD")
            conn_args = os.getenv(f"{client}_CONN_ARGS")
            databases = os.getenv(f"{client}_DATABASES", "").split(",")

            LOGGER.info(f"PostgresFactoryPreviewClient: Setting up PG Client {host}:{databases}")

            self.pg_preview_clients.append(PostgresPreviewClient(host=host, port=port, username=username, password=password, databases=databases, conn_args=conn_args))

    def is_supported_preview_source(self, params: Dict, optionalHeaders: Dict = None) -> bool:

        for client in self.pg_preview_clients:
            if client.is_supported_preview_source(params=params, optionalHeaders=optionalHeaders):
                LOGGER.info(f"PostgresFactoryPreviewClient: Found supported PG Client")
                return True

        LOGGER.info(f"PostgresFactoryPreviewClient: No supported PG Clients")

        return False

    def get_feature_preview_data(self, params: Dict, optionalHeaders: Dict = None) -> Response:
        pass

    def get_preview_data(self, params: Dict, optionalHeaders: Dict = None) -> Response:

        for client in self.pg_preview_clients:
            if client.is_supported_preview_source(params=params, optionalHeaders=optionalHeaders):
                return client.get_preview_data(params=params, optionalHeaders=optionalHeaders)

        return make_response(json.dumps({'preview_data': {}}), HTTPStatus.OK)
