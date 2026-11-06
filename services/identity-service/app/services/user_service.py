from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.audit_repository import AuditRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserInvite
from app.core.security import get_password_hash
from shared.core.exceptions import ConflictException, NotFoundException, ValidationException


class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.org_repo = OrganizationRepository(db)
        self.audit_repo = AuditRepository(db)

    def register_user(self, data: UserCreate, ip_address: str = None) -> UserResponse:
        # Check org exists
        org = self.org_repo.get_by_id(data.organization_id)
        if not org:
            raise NotFoundException(f"Organization '{data.organization_id}' not found.")

        # Check email uniqueness
        existing = self.user_repo.get_by_email(data.email)
        if existing:
            raise ConflictException(f"User with email '{data.email}' already exists.")

        roles = self.user_repo.get_or_create_roles(data.roles)
        hashed_pwd = get_password_hash(data.password)

        new_user = User(
            email=data.email,
            hashed_password=hashed_pwd,
            full_name=data.full_name,
            organization_id=data.organization_id,
            roles=roles,
            is_active=True,
            is_verified=True,
        )
        saved_user = self.user_repo.create(new_user)

        self.audit_repo.log(
            action="USER_REGISTERED",
            user_id=saved_user.id,
            organization_id=saved_user.organization_id,
            ip_address=ip_address,
            details=f"User {saved_user.email} registered with roles: {[r.name for r in saved_user.roles]}",
        )

        return UserResponse(
            id=saved_user.id,
            email=saved_user.email,
            full_name=saved_user.full_name,
            organization_id=saved_user.organization_id,
            is_active=saved_user.is_active,
            is_verified=saved_user.is_verified,
            roles=[r.name for r in saved_user.roles],
            created_at=saved_user.created_at,
            updated_at=saved_user.updated_at,
        )

    def list_users_in_org(self, organization_id: UUID) -> List[UserResponse]:
        users = self.user_repo.list_by_organization(organization_id)
        return [
            UserResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                organization_id=u.organization_id,
                is_active=u.is_active,
                is_verified=u.is_verified,
                roles=[r.name for r in u.roles],
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
            for u in users
        ]

