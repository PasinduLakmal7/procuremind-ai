"""Stateless JWT Token Validator and FastAPI Security Dependencies."""
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Set, Dict, Any
from uuid import UUID
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel, Field


class SecurityPrincipal(BaseModel):
    """Represents an authenticated caller extracted statelessly from a signed JWT."""
    user_id: UUID
    email: str
    organization_id: UUID
    roles: List[str] = Field(default_factory=list)

    def has_role(self, role: str) -> bool:
        return role in self.roles or "admin" in self.roles

    def has_any_role(self, *required_roles: str) -> bool:
        if "admin" in self.roles:
            return True
        return any(role in self.roles for role in required_roles)


def create_access_token(
    data: Dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed JWT access token for testing and services."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=2))
    to_encode.update({"exp": expire, "token_type": "access"})
    if "email" not in to_encode:
        to_encode["email"] = "user@example.com"
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def decode_jwt_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256"
) -> SecurityPrincipal:
    """Decodes and validates a JWT access token statelessly."""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        user_id_str = payload.get("sub")
        org_id_str = payload.get("organization_id")
        email = payload.get("email")
        roles = payload.get("roles", [])
        token_type = payload.get("token_type")

        if not user_id_str or not org_id_str or token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token claims. Expected access token with valid subject and organization.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return SecurityPrincipal(
            user_id=UUID(user_id_str),
            email=email or "",
            organization_id=UUID(org_id_str),
            roles=roles,
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(exc)}",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_principal_factory(secret_key: str, algorithm: str = "HS256"):
    """Factory creating a FastAPI dependency for extracting the SecurityPrincipal."""
    def get_current_principal(
        authorization: Optional[str] = Header(None, alias="Authorization")
    ) -> SecurityPrincipal:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or malformed Authorization header. Expected 'Bearer <token>'.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = authorization.split(" ")[1]
        return decode_jwt_token(token=token, secret_key=secret_key, algorithm=algorithm)

    return get_current_principal


def require_roles(*allowed_roles: str):
    """Enforces that the authenticated user possesses at least one of the specified roles."""
    def role_checker(principal: SecurityPrincipal = Depends(get_current_principal_factory("development-insecure-secret-key-change-in-production-min-32-chars"))):
        if not principal.has_any_role(*allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(allowed_roles)}",
            )
        return principal
    return role_checker
