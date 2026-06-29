"""
Audit service — записывает все значимые действия в audit_log
и создаёт Notification для администратора.
"""
from sqlalchemy.orm import Session

from app.models.models import AuditLog, Notification


class AuditService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def log(
        self,
        action: str,
        user_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        detail: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            detail=detail,
            ip_address=ip_address,
        )
        self._db.add(entry)
        self._db.flush()
        return entry

    def notify_admin(
        self,
        event: str,
        title: str,
        body: str | None = None,
        user_id: str | None = None,
        link: str | None = None,
    ) -> Notification:
        notif = Notification(
            event=event,
            title=title,
            body=body,
            user_id=user_id,
            link=link,
            is_read=False,
        )
        self._db.add(notif)
        self._db.flush()
        # Broadcast to admin WebSocket clients (fire-and-forget)
        try:
            import asyncio
            from app.api.ws import manager
            data = {
                "type": "notification",
                "event": event,
                "title": title,
                "body": body,
                "link": link,
            }
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(manager.broadcast_admins(data))
        except Exception:
            pass
        return notif
