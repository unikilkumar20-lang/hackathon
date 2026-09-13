import uuid
from typing import Any, List, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: List[Any] = []
    request_id: Optional[str] = None


class ErrorEnvelope(BaseModel):
    error: ErrorDetail


class AppException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[List[Any]] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Authentication required or token invalid", code: str = "UNAUTHORIZED"):
        super().__init__(code=code, message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenException(AppException):
    def __init__(self, message: str = "Access forbidden", code: str = "FORBIDDEN"):
        super().__init__(code=code, message=message, status_code=status.HTTP_403_FORBIDDEN)


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found", code: str = "NOT_FOUND"):
        super().__init__(code=code, message=message, status_code=status.HTTP_404_NOT_FOUND)


class ConflictException(AppException):
    def __init__(self, message: str = "Resource conflict", code: str = "CONFLICT"):
        super().__init__(code=code, message=message, status_code=status.HTTP_409_CONFLICT)


class ValidationException(AppException):
    def __init__(self, message: str, details: Optional[List[Any]] = None, code: str = "VALIDATION_ERROR"):
        super().__init__(code=code, message=message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)


class UnsupportedInputException(AppException):
    def __init__(self, message: str = "Unsupported input format or schema", details: Optional[List[Any]] = None):
        super().__init__(code="UNSUPPORTED_INPUT", message=message, status_code=status.HTTP_400_BAD_REQUEST, details=details)


class RateLimitedException(AppException):
    def __init__(self, message: str = "Rate limit exceeded. Please retry later."):
        super().__init__(code="RATE_LIMITED", message=message, status_code=status.HTTP_429_TOO_MANY_REQUESTS)


class ServiceUnavailableException(AppException):
    def __init__(self, message: str = "Service temporarily unavailable", code: str = "SERVICE_UNAVAILABLE"):
        super().__init__(code=code, message=message, status_code=status.HTTP_503_SERVICE_UNAVAILABLE)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    payload = {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
            "request_id": request_id,
        }
    }
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    payload = {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Input validation failed.",
            "details": exc.errors(),
            "request_id": request_id,
        }
    }
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content=payload)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    payload = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred.",
            "details": [],
            "request_id": request_id,
        }
    }
    return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content=payload)
