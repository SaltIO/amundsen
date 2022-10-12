
from http import HTTPStatus
import logging
from typing import Dict  # noqa: F401

from flask import Response, jsonify, make_response, current_app as app
from marshmallow import ValidationError
from pyarrow import flight

from amundsen_application.models.preview_data import PreviewData, PreviewDataSchema, ColumnItem
from amundsen_application.client.preview.source_selector_base_preview_client import SourceSelectorBasePreviewClient


class _DremioAuthHandler(flight.ClientAuthHandler):
    """ClientAuthHandler for connections to Dremio server endpoint.
    """
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password
        super(flight.ClientAuthHandler, self).__init__()

    def authenticate(self, outgoing, incoming) -> None:
        """Authenticate with Dremio user credentials.
        """
        basic_auth = flight.BasicAuth(self.username, self.password)
        outgoing.write(basic_auth.serialize())
        self.token = incoming.read()

    def get_token(self,) -> str:
        """Get the token from this AuthHandler.
        """
        return self.token


class DremioPreviewClient(SourceSelectorBasePreviewClient):

    SQL_STATEMENT = 'SELECT * FROM {schema}."{table}" LIMIT 50'

    def __init__(self,) -> None:
        self.url = app.config['PREVIEW_CLIENT_URL']
        self.username = app.config['PREVIEW_CLIENT_DREMIO_USERNAME']
        self.password = app.config['PREVIEW_CLIENT_DREMIO_PASSWORD']

        self.connection_args: Dict[str, bytes] = {}
        tls_root_certs_path = app.config['PREVIEW_CLIENT_DREMIO_CERTIFICATE']
        if tls_root_certs_path is not None:
            with open(tls_root_certs_path, "rb") as f:
                self.connection_args["tls_root_certs"] = f.read()

    def is_supported_preview_source(self, params: Dict, optionalHeaders: Dict = None) -> bool:
        warehouse_type = params.get('database')
        if warehouse_type is not None and \
           warehouse_type.lower() == 'dremio':
            return True
        else:
            return False

    def get_feature_preview_data(self, params: Dict, optionalHeaders: Dict = None) -> Response:
        """
        DremioPreviewClient only supports data preview currently but this function needs to be stubbed to
        implement the BasePreviewClient interface
        """
        pass

    def get_preview_data(self, params: Dict, optionalHeaders: Dict = None) -> Response:
        """Preview data from Dremio source
        """
        if not self.is_supported_preview_source(params, optionalHeaders):
            logging.info('Skipping table preview for non-Dremio table')
            return make_response(jsonify({'preview_data': {}}), HTTPStatus.OK)

        try:
            # Format base SQL_STATEMENT with request table and schema
            schema = '"{}"'.format(params['schema'].replace('.', '"."'))
            table = params['tableName']
            sql = DremioPreviewClient.SQL_STATEMENT.format(schema=schema,
                                                           table=table)

            client = flight.FlightClient(self.url, **self.connection_args)
            client.authenticate(_DremioAuthHandler(self.username, self.password))
            flight_descriptor = flight.FlightDescriptor.for_command(sql)
            flight_info = client.get_flight_info(flight_descriptor)
            reader = client.do_get(flight_info.endpoints[0].ticket)

            result = reader.read_all()
            names = result.schema.names
            types = result.schema.types

            columns = map(lambda x: x.to_pylist(), result.columns)
            rows = [dict(zip(names, row)) for row in zip(*columns)]
            column_items = [ColumnItem(n, t) for n, t in zip(names, types)]

            preview_data = PreviewData(column_items, rows)
            try:
                data = PreviewDataSchema().dump(preview_data)
                PreviewDataSchema().load(data)  # for validation only
                payload = jsonify({'preview_data': data})
                return make_response(payload, HTTPStatus.OK)
            except ValidationError as err:
                logging.error(f'Error(s) occurred while building preview data: {err.messages}')
                payload = jsonify({'preview_data': {}})
                return make_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)

        except Exception as e:
            logging.error(f'Encountered exception: {e}')
            payload = jsonify({'preview_data': {}})
            return make_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)