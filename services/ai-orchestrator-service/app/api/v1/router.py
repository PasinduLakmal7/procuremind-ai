from fastapi import APIRouter
from app.api.v1.endpoints import health, sample_protected, workflows

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(sample_protected.router)
api_router.include_router(workflows.router)
