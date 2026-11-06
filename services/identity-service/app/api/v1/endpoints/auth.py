from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    CurrentUserResponse,
)
from app.services.auth_service import AuthService
from app.core.rate_limit import auth_rate_limiter
from app.core.config import settings
from shared.auth.jwt_validator import get_current_principal_factory, SecurityPrincipal
from shared.api_contracts.responses import ApiResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

get_current_principal = get_current_principal_factory(
    secret_key=settings.JWT_SECRET_KEY,
    algorithm=settings.JWT_ALGORITHM,
)


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(
    request: Request,
    body: LoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticates credentials, generates JWT access and refresh tokens."""
    client_ip = request.client.host if request.client else "unknown"
    auth_rate_limiter.check_rate_limit(client_ip)

    service = AuthService(db)
    token_response = service.login(body, ip_address=client_ip)
    return ApiResponse(data=token_response, message="Authentication successful.")


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
def refresh_token(
    request: Request,
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """Exchanges a valid refresh token for a new access token and rotated refresh token."""
    client_ip = request.client.host if request.client else "unknown"
    service = AuthService(db)
    token_response = service.refresh(body.refresh_token, ip_address=client_ip)
    return ApiResponse(data=token_response, message="Token refreshed successfully.")


@router.post("/logout", response_model=ApiResponse[dict])
def logout(
    request: Request,
    body: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """Revokes the refresh token and ends the active session."""
    client_ip = request.client.host if request.client else "unknown"
    service = AuthService(db)
    service.logout(body.refresh_token, ip_address=client_ip)
    return ApiResponse(data={"logged_out": True}, message="Successfully logged out.")


@router.get("/me", response_model=ApiResponse[CurrentUserResponse])
def get_current_user(
    principal: SecurityPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    """Returns the authenticated user profile and roles."""
    service = AuthService(db)
    profile = service.get_current_user_profile(principal.user_id)
    return ApiResponse(data=profile)

