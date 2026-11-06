import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, CHAR
from app.db.base import Base


class GUID(TypeDecorator):
    """Platform-independent GUID/UUID type using CHAR(36)."""
    impl = CHAR(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        try:
            return uuid.UUID(str(value))
        except Exception:
            return value


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    registration_number = Column(String(100), nullable=True)
    industry = Column(String(100), default="Manufacturing", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")

