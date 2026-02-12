from __future__ import annotations

from typing import Any


class AppException(Exception):
    pass


class TenantNotFoundException(AppException):
    pass


class InvalidTenantException(AppException):
    pass


class DocumentNotFoundException(AppException):
    pass


class DocumentProcessingException(AppException):
    pass


class RAGException(AppException):
    pass


class OllamaException(AppException):
    pass


class ChromaException(AppException):
    pass


class DatabaseException(AppException):
    pass


class AuthenticationException(AppException):
    pass


class ValidationException(AppException):
    pass
