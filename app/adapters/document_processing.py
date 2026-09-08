from __future__ import annotations

from app.application.ports import ProcessedDocument
from app.services.document_processor import DocumentProcessor as LegacyProcessor


class DocumentProcessingAdapter:
    def __init__(self) -> None: self._processor = LegacyProcessor()
    def process(self, content_type: str, content: bytes) -> ProcessedDocument:
        _, chunks = self._processor.process_document(content_type, content)
        return ProcessedDocument(chunks)
