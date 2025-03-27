# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
from http import HTTPStatus
from typing import Any, Iterable, Mapping, Optional, Union

from amundsen_common.entity.resource_type import ResourceType
from amundsen_common.models.lineage import LineageSchema
from flasgger import swag_from
from flask import request
from flask_restful import Resource, reqparse

from amundsen_common.models.database import DatabaseSchema

from metadata_service.api import BaseAPI
from metadata_service.proxy import get_proxy_client
from metadata_service.auth import requires_auth


class DatabaseIdGET(BaseAPI):
    """
    DatabaseIdAPI supports GET operation to get a single cluster by its ID
    """
    def __init__(self) -> None:
        super().__init__(
            schema=DatabaseSchema,
            str_type='database',
            client=get_proxy_client(),
            id_qstring_key='id'
        )

    @requires_auth()
    @swag_from('swagger_doc/database/database_id_get.yml')
    def get(self, **kwargs: Optional[Any]) -> Iterable[Union[Mapping, int, None]]:
        return super().get(**kwargs)

class DatabaseGET(BaseAPI):
    """
    DatabaseAPI supports GET operation to get a single database by its composite key
    """
    def __init__(self) -> None:
        super().__init__(
            DatabaseSchema,
            'database',
            get_proxy_client()
        )

    @requires_auth()
    @swag_from('swagger_doc/database/database_get.yml')
    def get(self, *, database: str) -> Iterable[Union[Mapping, int, None]]:
        return super().get(database=database)

class DatabasesGET(BaseAPI):
    """
    ClustersAPI supports GET operation to get multiple clusters
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()
        super().__init__(DatabaseSchema, 'databases', self.client)

    @requires_auth()
    @swag_from('swagger_doc/database/databases_get.yml')
    def get(self) -> Iterable[Union[Mapping, int, None]]:
        return super().get()