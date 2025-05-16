
from typing import Dict, List
import logging

from metadata_service.ai.ai_embedding_client import AIEmbeddingClient

from sentence_transformers import SentenceTransformer


class STEmbeddingClient(AIEmbeddingClient):

    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.client = SentenceTransformer(STEmbeddingClient.EMBEDDING_MODEL)

    def create_embedding(self, embedding_input: str) -> List[float]:
        # embedding = self.client.encode(embedding_input, batch_size=32, show_progress_bar=True)
        embedding = self.client.encode(embedding_input, show_progress_bar=True, normalize_embeddings=True)

        return embedding.tolist()