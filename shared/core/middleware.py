"""HTTP Middlewares: Correlation ID and Exception Handling."""
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from shared.core.exceptions import AppException
from shared.api_contracts.responses import ErrorResponse, ErrorDetail


CORRELATION_ID_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Ensures every incoming request carries a correlation ID for tracing."""
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get(CORRELATION_ID_HEADER)
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
            
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers[CORRELATION_ID_HEADER] = correlation_id
        return response


def register_app_exception_handlers(app):
    """Registers standard exception handlers on a FastAPI application."""
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        correlation_id = getattr(request.state, "correlation_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=exc.code,
                    message=exc.message,
                    details=exc.details,
                    request_id=correlation_id,
                )
            ).model_dump(mode="json"),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        correlation_id = getattr(request.state, "correlation_id", None)
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(
                    code="INTERNAL_SERVER_ERROR",
                    message="An unexpected error occurred. Please contact system support.",
                    details=str(exc) if getattr(app.state, "debug", False) else None,
                    request_id=correlation_id,
                )
            ).model_dump(mode="json"),
        )

