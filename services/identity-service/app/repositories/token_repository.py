from datetime import datetime, timezone
from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.refresh_token import RefreshToken


class TokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_refresh_token(self, user_id: UUID, jti: str, expires_at: datetime) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            jti=jti,
            expires_at=expires_at,
            revoked=False,
        )
        self.db.add(token)
        self.db.commit()
        self.db.refresh(token)
        return token

    def get_by_jti(self, jti: str) -> Optional[RefreshToken]:
        return self.db.query(RefreshToken).filter(RefreshToken.jti == jti).first()

    def revoke_by_jti(self, jti: str) -> bool:
        token = self.get_by_jti(jti)
        if token:
            token.revoked = True
            self.db.commit()
            return True
        return False

    def revoke_all_for_user(self, user_id: UUID) -> int:
        count = self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False)
        ).update({"revoked": True})
        self.db.commit()
        return count

