import uuid
from sqlalchemy import Column, String, Table, ForeignKey
from app.db.base import Base
from app.models.organization import GUID

# Association table between users and roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", GUID(), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", GUID(), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)


class Role(Base):
    __tablename__ = "roles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

