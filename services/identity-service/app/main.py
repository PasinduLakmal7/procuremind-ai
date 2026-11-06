from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from shared.core.middleware import (
    CorrelationIdMiddleware,
    register_app_exception_handlers,
)
from shared.observability.logging import setup_logger

logger = setup_logger(
    service_name=settings.APP_NAME,
    log_level=settings.LOG_LEVEL,
    log_format=settings.LOG_FORMAT,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="Identity Service",
        description="User authentication, multi-tenancy organization management, and RBAC",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Distributed tracing correlation ID
    app.add_middleware(CorrelationIdMiddleware)

    # Standardized JSON error response handler
    register_app_exception_handlers(app)

    # Include API routes under prefix /api/v1/identity
    app.include_router(api_router, prefix="/api/v1/identity")

    # Also include health directly at root for container orchestrator probes
    from app.api.v1.endpoints import health
    app.include_router(health.router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)

