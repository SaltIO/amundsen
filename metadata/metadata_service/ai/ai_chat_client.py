
from typing import Dict, List
from abc import ABC, abstractmethod

from amundsen_common.models.ai import ChatResponse, ChatMessage


class AIChatClient(ABC):

    def __init__(self, **kwargs) -> None:
        pass

    @abstractmethod
    def chat(self, prompts: List[ChatMessage]) -> ChatResponse:
        pass
