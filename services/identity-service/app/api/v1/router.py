from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, organizations, health

api_router = APIRouter()

# Health checks at root or under /api/v1
api_router.include_router(health.router)

# Core identity endpoints
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(organizations.router)

