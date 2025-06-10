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
from metadata_service.auth import auth

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

    @auth.requires_auth()
    # @swag_from('swagger_doc/reveal/chat_post.yml')
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

# class RevealSearchAPI(Resource):
#     """
#     Reveal Search API
#     """

#     def __init__(self) -> None:
#         self.ai_chat_client: AIChatClient = OpenAIChatClient()
#         self.ai_embedding_client: AIEmbeddingClient = STEmbeddingClient()
#         self.search_service_base = current_app.config['SEARCHSERVICE_BASE']

#     @auth.requires_auth()
#     # @swag_from('swagger_doc/reveal/chat_post.yml')
#     def post(self, resource:str) -> Iterable[Union[Mapping, int, tuple, None]]:
#         try:
#             column_search_text: List[str] = self.get_column_search_text()

#             if not column_search_text:
#                 return {'message': 'column_search_text required'}, HTTPStatus.BAD_REQUEST

#             column_search_responses = []
#             for search_text in column_search_text:

#                 search_text_embedding = self.ai_embedding_client.create_embedding(embedding_input=search_text)

#                 search_payload = {
#                     "vector": search_text_embedding,
#                     "resource_type": resource.lower(),
#                     "results_count": 5
#                 }

#                 search_response = request_search(
#                     url=f"{self.search_service_base}/v2/knn_search",
#                     method="POST",
#                     json=search_payload
#                 )

#                 search_response: KnnSearchResponse = KnnSearchResponseSchema().loads(json.dumps(search_response.json()))

#                 if search_response.status_code == HTTPStatus.OK:
#                     column_search_hits = []
#                     for hit in search_response.results:
#                         column_search_hits.append(
#                             ColumnSearchHit(
#                                 score=hit.score,
#                                 key=hit.result['key'],
#                                 name=hit.result['name'],
#                                 table_key=hit.result['table_key'],
#                                 table_name=hit.result['table_name']
#                             )
#                         )

#                     column_search_responses.append(
#                         ColumnSearchResponse(
#                             search_text=search_text,
#                             hits=column_search_hits
#                         )
#                     )
#                 else:
#                     raise Exception(f"Failed to search: {search_response.msg}")

#             return ColumnSearchResponseSchema().dump(column_search_responses, many=True), HTTPStatus.OK

#         except Exception as e:
#             LOGGER.exception("Exception")
#             return {'message': 'internal server error'}, HTTPStatus.INTERNAL_SERVER_ERROR

#     def get_column_search_text(self) -> List[str]:
#         data = request.get_json(force=True)  # Force parsing regardless of Content-Type
#         if isinstance(data, str):  # If data is still a string, parse it manually
#             data = json.loads(data)

#         # LOGGER.info(f"data={data}")

#         if not data or 'column_search_text' not in data:
#             return None

#         return data['column_search_text']
