
from typing import Dict, List
from abc import ABC, abstractmethod


class AIEmbeddingClient(ABC):

    def __init__(self, **kwargs) -> None:
        pass

    @abstractmethod
    def create_embedding(self, embedding_input: str) -> List[float]:
        pass
