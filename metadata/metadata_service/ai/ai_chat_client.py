
from typing import Dict, List
from abc import ABC, abstractmethod

from amundsen_common.models.ai import ChatResponse, ChatMessage, ChatRequest


class AIChatClient(ABC):

    def __init__(self, **kwargs) -> None:
        pass

    @abstractmethod
    def chat(self, request: ChatRequest) -> ChatResponse:
        pass
