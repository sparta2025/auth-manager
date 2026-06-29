"""Token repository — v3 with ip_address and user_agent storage."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.models import AccessToken


class TokenRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, *, user_id: str, token: str, expires_at: datetime,
               ip_address: str | None = None, user_agent: str | None = None) -> AccessToken:
        record = AccessToken(
            user_id=user_id, token=token, expires_at=expires_at,
            ip_address=ip_address, user_agent=user_agent,
        )
        self._db.add(record)
        self._db.flush()
        return record

    def get_valid_token(self, token: str) -> AccessToken | None:
        now = datetime.now(timezone.utc)
        return (
            self._db.query(AccessToken)
            .filter(AccessToken.token == token, AccessToken.expires_at > now)
            .first()
        )

    def get_all_for_user(self, user_id: str) -> list[AccessToken]:
        return (
            self._db.query(AccessToken)
            .filter(AccessToken.user_id == user_id)
            .order_by(AccessToken.created_at.desc())
            .all()
        )

    def get_by_id(self, token_id: str) -> AccessToken | None:
        return self._db.query(AccessToken).filter(AccessToken.id == token_id).first()

    def delete(self, token_record: AccessToken) -> None:
        self._db.delete(token_record)
        self._db.flush()

    def delete_all_for_user(self, user_id: str) -> None:
        self._db.query(AccessToken).filter(AccessToken.user_id == user_id).delete()
        self._db.flush()
