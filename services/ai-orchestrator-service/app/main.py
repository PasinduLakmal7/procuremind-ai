from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from shared.core.middleware import CorrelationIdMiddleware, register_app_exception_handlers
from shared.observability.logging import setup_logger

logger = setup_logger(
    service_name=settings.APP_NAME,
    log_level=settings.LOG_LEVEL,
    log_format=settings.LOG_FORMAT,
)

def create_app() -> FastAPI:
    app = FastAPI(
        title="Ai Orchestrator Service",
        description="Microservice for ai-orchestrator-service",
        version="0.1.0",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(CorrelationIdMiddleware)
    register_app_exception_handlers(app)

    app.include_router(api_router, prefix="/api/v1/ai-orchestrator")

    from app.api.v1.endpoints import health
    app.include_router(health.router)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.PORT, reload=True)
