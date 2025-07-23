# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from http import HTTPStatus
from typing import (  # noqa: F401
    Any, Dict, Iterable, List,
)

from amundsen_common.models.search import (
    HighlightOptions, SearchRequestSchema, SearchResponseSchema, KnnSearchRequestSchema, KnnSearchResponseSchema
)
from flasgger import swag_from
from flask_restful import Resource, request

from search_service.proxy import get_proxy_client
from search_service.proxy.es_proxy_utils import RESOURCE_STR_MAPPING, Resource as AmundsenResource


LOGGER = logging.getLogger(__name__)


class SearchAPI(Resource):
    """
    Search API handles search requests for filtered and unfiltered search
    """

    def __init__(self) -> None:
        self.search_proxy = get_proxy_client()

    @swag_from('swagger_doc/search/search.yml')
    def post(self) -> Iterable[Any]:
        """
        Fetch search results
        :return: json payload of schema
        """
        request_json = request.get_json(force=True)
        LOGGER.info(f"SearchAPI:post()\n{request.json}")
        if not isinstance(request_json, dict):  # Ensure it's a dictionary
            request_json = json.loads(request_json)
        request_data = SearchRequestSchema().load(request_json, partial=False)
        LOGGER.info(f"request_data={request_data}")

        resources: List[AmundsenResource] = []
        highlight_options: Dict[AmundsenResource, HighlightOptions] = {}

        for r in request_data.resource_types:
            resource = RESOURCE_STR_MAPPING.get(r)
            if resource:
                resources.append(resource)
                if request_data.highlight_options.get(r):
                    highlight_options[resource] = request_data.highlight_options.get(r)
            else:
                err_msg = f'Search for invalid resource "{r}" requested'
                LOGGER.error(f"err_msg={err_msg}")
                return {'message': err_msg}, HTTPStatus.BAD_REQUEST

        try:
            search_results = self.search_proxy.search(query_term=request_data.query_term,
                                                      page_index=request_data.page_index,
                                                      results_per_page=request_data.results_per_page,
                                                      resource_types=resources,
                                                      filters=request_data.filters,
                                                      highlight_options=highlight_options)
            LOGGER.info(f"search_results={search_results}")
            return SearchResponseSchema().dump(search_results), HTTPStatus.OK

        except RuntimeError as e:
            err_msg = f'Exception encountered while processing search request {e}'
            LOGGER.error(f"err_msg={err_msg}")
            return {'message': err_msg}, HTTPStatus.INTERNAL_SERVER_ERROR

class KnnSearchAPI(Resource):
    """
    KNN Search API handles search requests for vector embedding search
    """

    def __init__(self) -> None:
        self.search_proxy = get_proxy_client()

    # @swag_from('swagger_doc/search/knn_search.yml')
    def post(self) -> Iterable[Any]:
        """
        Fetch search results
        :return: json payload of schema
        """
        request_json = request.get_json(force=True)
        LOGGER.info(f"KnnSearchAPI:post()\n{request.json}")
        if not isinstance(request_json, dict):  # Ensure it's a dictionary
            request_json = json.loads(request_json)
        request_data = KnnSearchRequestSchema().load(request_json, partial=False)
        LOGGER.info(f"request_data={request_data}")

        try:
            knn_search_results = self.search_proxy.knn_search(
                vector=request_data.vector,
                resource_type=RESOURCE_STR_MAPPING.get(request_data.resource_type),
                filters=request_data.filters,
                results_count=request_data.results_count
            )
            LOGGER.info(f"knn_search_results={knn_search_results}")
            return KnnSearchResponseSchema().dump(knn_search_results), HTTPStatus.OK
        except RuntimeError as e:
            err_msg = f'Exception encountered while processing KNN search request {e}'
            LOGGER.error(f"err_msg={err_msg}")
            return {'message': err_msg}, HTTPStatus.INTERNAL_SERVER_ERROR

