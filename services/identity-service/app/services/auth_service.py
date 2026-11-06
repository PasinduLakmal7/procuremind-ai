from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
)
from app.repositories.user_repository import UserRepository
from app.repositories.token_repository import TokenRepository
from app.repositories.audit_repository import AuditRepository
from app.schemas.auth import LoginRequest, TokenResponse, CurrentUserResponse
from shared.core.exceptions import UnauthorizedException, ForbiddenException, NotFoundException


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_repo = TokenRepository(db)
        self.audit_repo = AuditRepository(db)

    def login(self, data: LoginRequest, ip_address: Optional[str] = None) -> TokenResponse:
        user = self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            self.audit_repo.log(
                action="USER_LOGIN_FAILURE",
                user_id=user.id if user else None,
                organization_id=user.organization_id if user else None,
                status="FAILURE",
                ip_address=ip_address,
                details=f"Invalid credentials attempt for email: {data.email}",
            )
            raise UnauthorizedException("Invalid email or password.")

        if not user.is_active:
            self.audit_repo.log(
                action="USER_LOGIN_LOCKED",
                user_id=user.id,
                organization_id=user.organization_id,
                status="FAILURE",
                ip_address=ip_address,
                details="Inactive user tried to log in",
            )
            raise ForbiddenException("Account is inactive. Contact organization administrator.")

        role_names = [r.name for r in user.roles]
        access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            organization_id=str(user.organization_id),
            roles=role_names,
        )

        refresh_token, jti, expire = create_refresh_token(user_id=str(user.id))
        self.token_repo.save_refresh_token(user_id=user.id, jti=jti, expires_at=expire)

        self.audit_repo.log(
            action="USER_LOGIN_SUCCESS",
            user_id=user.id,
            organization_id=user.organization_id,
            status="SUCCESS",
            ip_address=ip_address,
            details=f"User {user.email} logged in successfully",
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            organization_id=user.organization_id,
            roles=role_names,
        )

    def refresh(self, refresh_token_str: str, ip_address: Optional[str] = None) -> TokenResponse:
        try:
            payload = jwt.decode(
                refresh_token_str,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            token_type = payload.get("token_type")
            jti = payload.get("jti")
            user_id_str = payload.get("sub")

            if token_type != "refresh" or not jti or not user_id_str:
                raise UnauthorizedException("Invalid refresh token claims.")

        except JWTError as exc:
            raise UnauthorizedException(f"Invalid or expired refresh token: {str(exc)}")

        token_record = self.token_repo.get_by_jti(jti)
        if not token_record or token_record.revoked:
            raise UnauthorizedException("Refresh token is invalid or has been revoked.")

        now_utc = datetime.now(timezone.utc)
        # Handle naive datetime from db
        exp_at = token_record.expires_at
        if exp_at.tzinfo is None:
            exp_at = exp_at.replace(tzinfo=timezone.utc)

        if exp_at < now_utc:
            raise UnauthorizedException("Refresh token has expired.")

        # Revoke old refresh token (token rotation)
        self.token_repo.revoke_by_jti(jti)

        user = self.user_repo.get_by_id(UUID(user_id_str))
        if not user or not user.is_active:
            raise UnauthorizedException("User not found or inactive.")

        role_names = [r.name for r in user.roles]
        new_access_token = create_access_token(
            user_id=str(user.id),
            email=user.email,
            organization_id=str(user.organization_id),
            roles=role_names,
        )

        new_refresh_token, new_jti, new_expire = create_refresh_token(user_id=str(user.id))
        self.token_repo.save_refresh_token(user_id=user.id, jti=new_jti, expires_at=new_expire)

        self.audit_repo.log(
            action="TOKEN_REFRESH_SUCCESS",
            user_id=user.id,
            organization_id=user.organization_id,
            status="SUCCESS",
            ip_address=ip_address,
            details=f"Token refreshed for user {user.email}",
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            organization_id=user.organization_id,
            roles=role_names,
        )

    def logout(self, refresh_token_str: str, ip_address: Optional[str] = None) -> None:
        try:
            payload = jwt.decode(
                refresh_token_str,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            jti = payload.get("jti")
            user_id_str = payload.get("sub")
            if jti:
                self.token_repo.revoke_by_jti(jti)
            if user_id_str:
                self.audit_repo.log(
                    action="USER_LOGOUT",
                    user_id=UUID(user_id_str),
                    status="SUCCESS",
                    ip_address=ip_address,
                    details="User logged out and session revoked",
                )
        except JWTError:
            pass  # Best effort revocation

    def get_current_user_profile(self, user_id: UUID) -> CurrentUserResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("User profile not found.")
        return CurrentUserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            organization_id=user.organization_id,
            organization_name=user.organization.name if user.organization else None,
            roles=[r.name for r in user.roles],
            is_active=user.is_active,
        )

