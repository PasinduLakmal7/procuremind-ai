from fastapi import APIRouter
from app.api.v1.endpoints import health, sample_protected, purchase_requests

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(sample_protected.router)
api_router.include_router(purchase_requests.router)
