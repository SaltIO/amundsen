from http import HTTPStatus
from typing import Any, Iterable, Mapping, Optional, Union

from flasgger import swag_from
from flask import request
from flask_restful import reqparse

from amundsen_common.models.schema import SchemaSchema

from metadata_service.api import BaseAPI
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client
from ddp_auth.flask import require_auth


class SchemaIdGET(BaseAPI):
    """
    SchemaAPI supports GET operation to get a single schema by its ID
    """
    def __init__(self) -> None:
        super().__init__(
            schema=SchemaSchema,
            str_type='schema',
            client=get_proxy_client(),
            id_qstring_key='id'
        )

    @require_auth()
    @swag_from('swagger_doc/schema/schema_id_get.yml')
    def get(self, **kwargs: Optional[Any]) -> Iterable[Union[Mapping, int, None]]:
        return super().get(**kwargs)

class SchemaGET(BaseAPI):
    """
    SchemaAPI supports GET operation to get a single schema by its composite key
    """
    def __init__(self) -> None:
        super().__init__(
            SchemaSchema,
            'schema',
            get_proxy_client()
        )

    @require_auth()
    @swag_from('swagger_doc/schema/schema_get.yml')
    def get(self, *, database: str, cluster: str, schema: str) -> Iterable[Union[Mapping, int, None]]:
        return super().get(database=database, cluster=cluster, schema=schema)

class SchemasGET(BaseAPI):
    """
    SchemasAPI supports GET operation to get multiple schemas
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()
        super().__init__(SchemaSchema, 'schemas', self.client)

    @require_auth()
    @swag_from('swagger_doc/schema/schemas_get.yml')
    def get(self, *, database: Optional[str] = None, cluster: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        return super().get(database=database, cluster=cluster)