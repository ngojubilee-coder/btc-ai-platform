"""Embeddings generation for RAG — uses Gemini embeddings, falls back to hash-based dummy."""
import hashlib
import numpy as np
from core.config import settings
from core.logging_config import logger


class EmbeddingService:
    def __init__(self):
        self._client = None
        self._provider = None

    @property
    def client(self):
        if self._client is None:
            if settings.gemini_api_key and settings.gemini_api_key != "your-gemini-key":
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=settings.gemini_api_key)
                    self._client = genai
                    self._provider = "gemini"
                except Exception:
                    pass
            if self._client is None and settings.openai_api_key and settings.openai_api_key != "your-openai-key":
                try:
                    from openai import OpenAI
                    self._client = OpenAI(api_key=settings.openai_api_key)
                    self._provider = "openai"
                except Exception:
                    pass
        return self._client

    def embed(self, text: str) -> list[float]:
        if not self.client:
            return self._dummy_embedding(text)
        try:
            if self._provider == "gemini":
                resp = self.client.embed_content(
                    model="models/gemini-embedding-001",
                    content=text,
                    task_type="retrieval_document",
                )
                return resp["embedding"]
            else:
                resp = self.client.embeddings.create(
                    model=settings.embedding_model,
                    input=text,
                )
                return resp.data[0].embedding
        except Exception as e:
            logger.warning(f"[Embeddings] Error: {e}, using dummy")
            return self._dummy_embedding(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not self.client:
            return [self._dummy_embedding(t) for t in texts]
        try:
            if self._provider == "gemini":
                resp = self.client.embed_content(
                    model="models/gemini-embedding-001",
                    content=texts,
                    task_type="retrieval_document",
                )
                return [e for e in resp["embedding"]]
            else:
                resp = self.client.embeddings.create(
                    model=settings.embedding_model,
                    input=texts,
                )
                return [d.embedding for d in resp.data]
        except Exception as e:
            logger.warning(f"[Embeddings] Batch error: {e}, using dummy")
            return [self._dummy_embedding(t) for t in texts]

    def _dummy_embedding(self, text: str) -> list[float]:
        h = hashlib.sha256(text.encode()).digest()
        return list(np.frombuffer(h[:6] + b"\x00" * (settings.embedding_dimensions * 4 - 6), dtype=np.uint8).astype(float)[:settings.embedding_dimensions])


embedding_service = EmbeddingService()
