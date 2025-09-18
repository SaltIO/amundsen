# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
from abc import ABC, abstractmethod
from typing import List

from sentence_transformers import SentenceTransformer

LOGGER = logging.getLogger(__name__)


class EmbeddingService(ABC):
    """Abstract base class for embedding services."""
    
    @abstractmethod
    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Encode a list of texts into embeddings.
        
        Args:
            texts: List of text strings to encode
            
        Returns:
            List of embedding vectors
        """
        pass


class SentenceTransformersService(EmbeddingService):
    """Sentence Transformers implementation of embedding service."""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        Initialize the sentence transformers service.
        
        Args:
            model_name: Name of the sentence transformers model to use
        """
        self.model = SentenceTransformer(model_name)
        LOGGER.info(f"Initialized SentenceTransformers service with model: {model_name}")
    
    def encode(self, texts: List[str]) -> List[List[float]]:
        """
        Encode texts using sentence transformers.
        
        Args:
            texts: List of text strings to encode
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = self.model.encode(texts).tolist()
            LOGGER.info(f"Generated {len(embeddings)} embeddings from {len(texts)} texts")
            return embeddings
        except Exception as e:
            LOGGER.error(f"Failed to generate embeddings: {e}")
            raise


# Global embedding service instance
_embedding_service: EmbeddingService = None


def get_embedding_service() -> EmbeddingService:
    """
    Get the global embedding service instance.
    Creates a default SentenceTransformers service if none exists.
    
    Returns:
        EmbeddingService instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = SentenceTransformersService()
    return _embedding_service


def set_embedding_service(service: EmbeddingService) -> None:
    """
    Set the global embedding service instance.
    
    Args:
        service: EmbeddingService instance to use
    """
    global _embedding_service
    _embedding_service = service 