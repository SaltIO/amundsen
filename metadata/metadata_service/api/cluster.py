from http import HTTPStatus
from typing import Any, Iterable, Mapping, Optional, Union

from flasgger import swag_from
from flask import request
from flask_restful import reqparse

from amundsen_common.models.cluster import ClusterSchema

from metadata_service.api import BaseAPI
from metadata_service.exception import NotFoundException
from metadata_service.proxy import get_proxy_client
from metadata_service.auth import requires_auth


class ClusterIdGET(BaseAPI):
    """
    ClusterAPI supports GET operation to get a single cluster by its ID
    """
    def __init__(self) -> None:
        super().__init__(
            schema=ClusterSchema,
            str_type='cluster',
            client=get_proxy_client(),
            id_qstring_key='id'
        )

    @swag_from('swagger_doc/cluster/cluster_id_get.yml')
    def get(self, **kwargs: Optional[Any]) -> Iterable[Union[Mapping, int, None]]:
        return super().get(**kwargs)

class ClusterGET(BaseAPI):
    """
    ClusterAPI supports GET operation to get a single cluster by its composite key
    """
    def __init__(self) -> None:
        super().__init__(
            ClusterSchema,
            'cluster',
            get_proxy_client()
        )

    @requires_auth()
    @swag_from('swagger_doc/cluster/cluster_get.yml')
    def get(self, *, database: str, cluster: str) -> Iterable[Union[Mapping, int, None]]:
        return super().get(database=database, cluster=cluster)

class ClustersGET(BaseAPI):
    """
    ClustersAPI supports GET operation to get multiple clusters
    """
    def __init__(self) -> None:
        self.client = get_proxy_client()
        super().__init__(ClusterSchema, 'clusters', self.client)

    @requires_auth()
    @swag_from('swagger_doc/cluster/clusters_get.yml')
    def get(self, *, database: Optional[str] = None) -> Iterable[Union[Mapping, int, None]]:
        return super().get(database=database)