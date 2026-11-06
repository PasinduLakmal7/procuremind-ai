"""Standard application error definitions."""
from typing import Any, Dict, Optional


class AppException(Exception):
    """Base application exception with error code and HTTP status code."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class BadRequestException(AppException):
    def __init__(self, message: str = "Bad request", code: str = "BAD_REQUEST", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=400, details=details)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=404, details=details)


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized", code: str = "UNAUTHORIZED", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=401, details=details)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Access forbidden", code: str = "FORBIDDEN", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=403, details=details)


class ConflictException(AppException):
    def __init__(self, message: str = "Resource conflict", code: str = "CONFLICT", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=409, details=details)


class ValidationException(AppException):
    def __init__(self, message: str = "Validation failed", code: str = "VALIDATION_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=422, details=details)


class RateLimitExceededException(AppException):
    def __init__(self, message: str = "Rate limit exceeded. Please try again later.", code: str = "RATE_LIMIT_EXCEEDED", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, code=code, status_code=429, details=details)
