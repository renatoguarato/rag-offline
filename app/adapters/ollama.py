from __future__ import annotations

from app.services.ollama_service import OllamaService


class OllamaAdapter:
    def __init__(self) -> None: self._service = OllamaService()
    async def embed(self, texts: list[str]) -> list[list[float]]: return await self._service.generate_embeddings(texts)
    async def answer(self, question: str, context: str) -> str: return await self._service.generate_response(question, context)
    async def is_available(self) -> bool: return await self._service.check_connection()
