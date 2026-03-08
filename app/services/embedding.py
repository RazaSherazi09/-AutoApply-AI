"""
Singleton embedding service using sentence-transformers.

Uses BAAI/bge-base-en-v1.5 — a high-quality pretrained HuggingFace model
that outperforms MiniLM on semantic similarity benchmarks (MTEB).
Loads the model once, stores embeddings as float32 bytes.
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

import numpy as np
from loguru import logger

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Thread-safe singleton for the sentence-transformers model.

    Usage::

        svc = EmbeddingService.get_instance()
        emb = svc.encode("some text")
        raw = EmbeddingService.to_bytes(emb)
        restored = EmbeddingService.from_bytes(raw)
    """

    _instance: EmbeddingService | None = None
    _lock = threading.Lock()
    _model: SentenceTransformer | None = None

    MODEL_NAME = "BAAI/bge-base-en-v1.5"

    def __init__(self) -> None:
        raise RuntimeError("Use EmbeddingService.get_instance()")

    @classmethod
    def get_instance(cls) -> EmbeddingService:
        """Return the singleton instance, creating it on first call."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # double-checked locking
                    instance = object.__new__(cls)
                    cls._instance = instance
                    cls._load_model()
        return cls._instance

    @classmethod
    def _load_model(cls) -> None:
        """Load the sentence-transformer model (called once)."""
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformer model: {}", cls.MODEL_NAME)
            cls._model = SentenceTransformer(cls.MODEL_NAME)
            logger.info("Model loaded successfully")
        except ImportError:
            logger.warning("sentence-transformers not found! Using mock embeddings.")
            cls._model = "MOCK"
        except Exception as e:
            logger.warning(f"Failed to load sentence-transformer model: {e}. Using mock embeddings.")
            cls._model = "MOCK"

    def encode(self, text: str) -> np.ndarray:
        """
        Encode text into a normalized float32 embedding vector.

        Args:
            text: Input text to encode.

        Returns:
            1-D numpy float32 array (L2-normalized).
        """
        if self._model == "MOCK":
            # Return dummy 384-length zero vector (compatible with existing DB)
            return np.zeros(384, dtype=np.float32)
            
        assert self._model is not None, "Model not loaded"
        return self._model.encode(text, normalize_embeddings=True).astype(np.float32)

    def encode_batch(self, texts: list[str]) -> np.ndarray:
        """
        Encode a batch of texts.

        Args:
            texts: List of input texts.

        Returns:
            2-D numpy array of shape (N, dim), each row L2-normalized.
        """
        if self._model == "MOCK":
            return np.zeros((len(texts), 384), dtype=np.float32)
            
        assert self._model is not None, "Model not loaded"
        return self._model.encode(texts, normalize_embeddings=True).astype(np.float32)

    # ── Serialization helpers ──

    @staticmethod
    def to_bytes(emb: np.ndarray) -> bytes:
        """Pack a numpy float32 array into raw bytes for DB storage."""
        return emb.astype(np.float32).tobytes()

    @staticmethod
    def from_bytes(data: bytes) -> np.ndarray:
        """Unpack raw bytes back into a numpy float32 array."""
        return np.frombuffer(data, dtype=np.float32).copy()

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """
        Compute cosine similarity between two L2-normalized vectors.

        Since vectors are already normalized, this is just the dot product.

        Returns:
            Similarity score in [-1, 1].
        """
        return float(np.dot(a, b))
