from __future__ import annotations

from typing import List, Optional

import httpx
from ollama import AsyncClient

from app.core.config import settings
from app.core.exceptions import OllamaException
from app.core.logging import get_logger

logger = get_logger(__name__)


class OllamaService:
    def __init__(self) -> None:
        self.client = AsyncClient(host=settings.OLLAMA_BASE_URL)
        self.model = settings.OLLAMA_MODEL
        logger.info(f"Ollama client initialized with model: {self.model}")

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = []

        for text in texts:
            try:
                response = await self.client.embeddings(model=self.model, prompt=text)
                embeddings.append(response["embedding"])
            except Exception as e:
                logger.error(f"Failed to generate embedding: {e}")
                raise OllamaException(f"Failed to generate embedding: {e}")

        logger.info(f"Generated {len(embeddings)} embeddings")
        return embeddings

    async def generate_response(self, prompt: str, context: Optional[str] = None) -> str:
        system_prompt = (
            "You are a helpful assistant that answers questions based on the "
            "provided context. If the answer cannot be found in the context, "
            "say so clearly. Be concise and accurate."
        )

        if context:
            full_prompt = f"Context:\n{context}\n\nQuestion: {prompt}"
        else:
            full_prompt = prompt

        try:
            response = await self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt},
                ],
            )
            result = response["message"]["content"]
            logger.info(f"Generated response for prompt: {prompt[:50]}...")
            return result
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise OllamaException(f"Failed to generate response: {e}")

    async def check_connection(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                response.raise_for_status()
            logger.info("Ollama connection check successful")
            return True
        except Exception as e:
            logger.error(f"Ollama connection check failed: {e}")
            return False


ollama_service = OllamaService()
