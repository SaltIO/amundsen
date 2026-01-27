# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import json
import logging
import ast
from http import HTTPStatus
from typing import Any, Dict, Iterable, List, Mapping, Optional, Union

from flasgger import swag_from
from flask import request, current_app
from flask_restful import Resource

from metadata_service.ai.ai_chat_client import AIChatClient
from metadata_service.ai.ai_embedding_client import AIEmbeddingClient
from metadata_service.ai.openai_client import OpenAIChatClient
from metadata_service.ai.st_embedding_client import STEmbeddingClient
from metadata_service.api.utils.request_utils import request_search
from ddp_auth.flask_api_keys import require_auth

from amundsen_common.models.search import KnnSearchResponseSchema, KnnSearchResponse
from amundsen_common.models.ai import (
    ColumnSearchHit, ColumnSearchResponse, ColumnSearchResponseSchema,
    ChatResponse, ChatResponseSchema, ChatMessage, ChatMessageSchema, ChatRequest, ChatRequestSchema
)


LOGGER = logging.getLogger(__name__)


class RevealChatAPI(Resource):
    """
    Reveal Chat API
    """

    def __init__(self) -> None:
        self.ai_chat_client: AIChatClient = OpenAIChatClient()

    @require_auth()
    @swag_from('swagger_doc/reveal/chat_post.yml')
    def post(self) -> Iterable[Union[Mapping, int, tuple, None]]:
        try:
            request = self.get_chat_request()

            if not request:
                return {'message': 'request required'}, HTTPStatus.BAD_REQUEST

            chat_response: ChatResponse = self.ai_chat_client.chat(request=request)
            return ChatResponseSchema().dump(chat_response), HTTPStatus.OK

        except Exception:
            LOGGER.exception("Chat API Error: ")
            return {'message': 'internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR

    def get_chat_request(self) -> ChatRequest:
        data = request.get_json(force=True)  # Force parsing regardless of Content-Type
        if isinstance(data, str):  # If data is still a string, parse it manually
            data = json.loads(data)

        LOGGER.info(f"data={data}")

        if not data:
            return None

        return ChatRequestSchema().load(data)

class RevealSearchAPI(Resource):
    """
    Reveal Search API
    """

    def __init__(self) -> None:
        self.ai_chat_client: AIChatClient = OpenAIChatClient()
        self.ai_embedding_client: AIEmbeddingClient = STEmbeddingClient()

    @require_auth()
    @swag_from('swagger_doc/reveal/search_post.yml')
    def post(self, resource:str) -> Iterable[Union[Mapping, int, tuple, None]]:
        try:
            if resource == 'column':
                data = request.get_json(force=True)  # Force parsing regardless of Content-Type
                if isinstance(data, str):  # If data is still a string, parse it manually
                    data = json.loads(data)

                # LOGGER.info(f"data={data}")

                if not data or 'column_search_text' not in data:
                    return {'message': 'column_search_text required'}, HTTPStatus.BAD_REQUEST

                column_search_text = data['column_search_text']

                filters = []
                if 'search_filters' in data:
                    for filter in data['search_filters']:
                        filters.append({
                            "name": filter['name'],
                            "values": filter['values'],
                            "operation": filter['operation']
                        })


                column_search_responses = []
                for search_text in column_search_text:

                    search_text_embedding = self.ai_embedding_client.create_embedding(embedding_input=search_text)

                    search_payload = {
                        "vector": search_text_embedding,
                        "resource_type": resource.lower(),
                        "filters": filters,
                        "results_count": 5
                    }

                    search_response = request_search(
                        url="/v2/knn_search",
                        method="POST",
                        json=search_payload
                    )

                    search_response: KnnSearchResponse = KnnSearchResponseSchema().loads(json.dumps(search_response.json()))

                    if search_response.status_code == HTTPStatus.OK:
                        column_search_hits = []
                        for hit in search_response.results:
                            column_search_hits.append(
                                ColumnSearchHit(
                                    score=hit.score,
                                    key=hit.result['key'],
                                    name=hit.result['name'],
                                    data_type=hit.result.get('data_type', None),
                                    description=hit.result.get('description', None),
                                    table_key=hit.result['table_key'],
                                    table_name=hit.result['table_name'],
                                    table_description=hit.result.get('table_description', None),
                                )
                            )

                        column_search_responses.append(
                            ColumnSearchResponse(
                                search_text=search_text,
                                hits=column_search_hits
                            )
                        )
                    else:
                        raise Exception(f"Failed to search: {search_response.msg}")

                return ColumnSearchResponseSchema().dump(column_search_responses, many=True), HTTPStatus.OK
            else:
                raise ValueError(f'Unknown resource type {resource}')

        except Exception as e:
            LOGGER.exception("Exception")
            return {'message': 'internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR

