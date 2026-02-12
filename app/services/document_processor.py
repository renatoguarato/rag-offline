from __future__ import annotations

import hashlib
from io import BytesIO
from typing import List, Tuple

import numpy as np
from docx import Document as DocxDocument
from pypdf import PdfReader

from app.core.exceptions import DocumentProcessingException
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentProcessor:
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        try:
            reader = PdfReader(BytesIO(file_content))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            logger.info(f"Extracted text from PDF: {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from PDF: {e}")
            raise DocumentProcessingException(f"Failed to extract text from PDF: {e}")

    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        try:
            doc = DocxDocument(BytesIO(file_content))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            logger.info(f"Extracted text from DOCX: {len(text)} characters")
            return text
        except Exception as e:
            logger.error(f"Failed to extract text from DOCX: {e}")
            raise DocumentProcessingException(f"Failed to extract text from DOCX: {e}")

    @staticmethod
    def extract_text_from_txt(file_content: bytes) -> str:
        try:
            text = file_content.decode("utf-8")
            logger.info(f"Extracted text from TXT: {len(text)} characters")
            return text
        except UnicodeDecodeError:
            try:
                text = file_content.decode("latin-1")
                logger.info(f"Extracted text from TXT (latin-1): {len(text)} characters")
                return text
            except Exception as e:
                logger.error(f"Failed to extract text from TXT: {e}")
                raise DocumentProcessingException(f"Failed to extract text from TXT: {e}")

    @staticmethod
    def chunk_text(text: str) -> List[str]:
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + DocumentProcessor.CHUNK_SIZE

            if end >= text_length:
                chunks.append(text[start:].strip())
                break

            chunk = text[start:end]
            last_period = chunk.rfind(".")
            last_newline = chunk.rfind("\n")
            split_point = max(last_period, last_newline)

            if split_point > DocumentProcessor.CHUNK_SIZE // 2:
                end = start + split_point + 1
                chunk = text[start:end]

            chunks.append(chunk.strip())
            start = end - DocumentProcessor.CHUNK_OVERLAP

        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks

    @staticmethod
    def process_document(content_type: str, file_content: bytes) -> Tuple[str, List[str]]:
        content_type_lower = content_type.lower()

        if "pdf" in content_type_lower:
            text = DocumentProcessor.extract_text_from_pdf(file_content)
        elif "docx" in content_type_lower or "word" in content_type_lower:
            text = DocumentProcessor.extract_text_from_docx(file_content)
        elif "text" in content_type_lower or "txt" in content_type_lower:
            text = DocumentProcessor.extract_text_from_txt(file_content)
        else:
            raise DocumentProcessingException(f"Unsupported content type: {content_type}")

        if not text.strip():
            raise DocumentProcessingException("Extracted text is empty")

        chunks = DocumentProcessor.chunk_text(text)
        return text, chunks


document_processor = DocumentProcessor()
