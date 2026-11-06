from typing import List
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import UserService
from app.core.config import settings
from shared.auth.jwt_validator import get_current_principal_factory, SecurityPrincipal
from shared.api_contracts.responses import ApiResponse
from shared.core.exceptions import ForbiddenException

router = APIRouter(prefix="/users", tags=["Users"])

get_current_principal = get_current_principal_factory(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)


@router.post("/register", response_model=ApiResponse[UserResponse])
def register_user(
    request: Request,
    body: UserCreate,
    db: Session = Depends(get_db),
):
    """Registers a new user within an organization."""
    client_ip = request.client.host if request.client else "unknown"
    service = UserService(db)
    user = service.register_user(body, ip_address=client_ip)
    return ApiResponse(data=user, message="User registered successfully.")


@router.get("", response_model=ApiResponse[List[UserResponse]])
def list_users(
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Lists users belonging to the authenticated caller's organization."""
    service = UserService(db)
    users = service.list_users_in_org(principal.organization_id)
    return ApiResponse(data=users)

