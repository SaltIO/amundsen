
from typing import Dict, List
import logging
import os
from http import HTTPStatus
from typing import Dict  # noqa: F401
import json

from metadata_service.ai.ai_chat_client import AIChatClient
from metadata_service.ai.ai_embedding_client import AIEmbeddingClient
from openai import OpenAI

from flask import current_app, make_response

from amundsen_common.models.ai import ChatResponse, ChatMessage, ChatMessageSchema, ChatRequest

LOGGER = logging.getLogger(__name__)


class OpenAIChatClient(AIChatClient, AIEmbeddingClient):

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        api_key = current_app.config.get('AI_GPT_CLIENT_API_KEY')
        self.client = OpenAI(
            api_key=api_key
        )
        # openai.api_key = os.getenv("GPT_CLIENT_API_KEY")
        self.model = current_app.config.get('AI_GPT_CLIENT_API_MODEL')
        self.default_system_message = current_app.config.get('AI_GPT_CLIENT_API_DEFAULT_SYSTEM_MESSAGE')

        LOGGER.info(f'default_system_message={self.default_system_message}')
        LOGGER.info(f'api_key={api_key}')
        LOGGER.info(f'model={self.model}')

    def chat(self, request: ChatRequest) -> ChatResponse:
        chat_response: ChatResponse = None

        LOGGER.info(f"request={request}")

        if not request or not request.messages or len(request.messages) == 0:
            return make_response({"message": "prompts required"}, HTTPStatus.INTERNAL_SERVER_ERROR)

        if self.default_system_message:
            request.messages.insert(0, ChatMessage(role="system", content=self.default_system_message))

        try:
            chat_completion = self.client.chat.completions.create(
                model=self.model,
                messages=ChatMessageSchema().dump(request.messages, many=True),
                functions=request.function.functions if request.function else None,
                function_call=request.function.function_call if request.function else None
            )

            finish_reason = chat_completion.choices[0].finish_reason
            content = chat_completion.choices[0].message.content
            role = chat_completion.choices[0].message.role
            function_call = chat_completion.choices[0].message.function_call

            LOGGER.info(f"chat_completion={chat_completion}")
            LOGGER.info(f"finish_reason={finish_reason}")
            LOGGER.info(f"content={content}")
            LOGGER.info(f"role={role}")
            LOGGER.info(f"function_call={function_call}")

            chat_response = ChatResponse(
                finish_reason=finish_reason,
                message=ChatMessage(
                    content=content,
                    role=role
                ),
                function_call=function_call.model_dump() if function_call else None
            )

        except Exception as ex:
            msg = f"Failed to get chat response from Open AI"
            LOGGER.exception(msg)
            raise ex

        return chat_response

    def create_embedding(self, embedding_input: str) -> List[float]:
        embedding = self.client.embeddings.create(
            input=embedding_input,
            model=self.embedding_model
        )

        return embedding.data[0].embedding