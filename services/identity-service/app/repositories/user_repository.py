from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email.ilike(email)).first()

    def list_by_organization(self, organization_id: UUID, skip: int = 0, limit: int = 100) -> List[User]:
        return self.db.query(User).filter(User.organization_id == organization_id).offset(skip).limit(limit).all()

    def get_role_by_name(self, name: str) -> Optional[Role]:
        return self.db.query(Role).filter(Role.name == name).first()

    def get_or_create_roles(self, role_names: List[str]) -> List[Role]:
        roles = []
        for name in role_names:
            role = self.get_role_by_name(name)
            if not role:
                role = Role(name=name, description=f"Role for {name}")
                self.db.add(role)
                self.db.flush()
            roles.append(role)
        return roles

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User) -> User:
        self.db.commit()
        self.db.refresh(user)
        return user

