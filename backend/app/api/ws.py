"""
WebSocket endpoint для real-time уведомлений администратора.

Клиент подключается к ws://host/ws/notifications?token=<access_token>.
При создании нового Notification в БД — сервер pushes JSON в открытые соединения.

Архитектура:
  - Менеджер соединений хранит множество активных WebSocket-ов.
  - broadcast() вызывается из AuditService после notify_admin().
  - При горизонтальном масштабировании заменить на Redis pub/sub.
"""
import asyncio
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.token_repo import TokenRepository

log = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Thread-safe менеджер WebSocket-соединений."""

    def __init__(self):
        # user_id → set of WebSocket
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self._connections.setdefault(user_id, set()).add(websocket)
        log.info("WS connected: user=%s total=%d", user_id, self.count())

    def disconnect(self, websocket: WebSocket, user_id: str):
        conns = self._connections.get(user_id, set())
        conns.discard(websocket)
        if not conns:
            self._connections.pop(user_id, None)
        log.info("WS disconnected: user=%s", user_id)

    async def send_to_user(self, user_id: str, data: dict[str, Any]):
        payload = json.dumps(data, ensure_ascii=False)
        dead = set()
        for ws in self._connections.get(user_id, set()):
            try:
                await ws.send_text(payload)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self._connections.get(user_id, set()).discard(ws)

    async def broadcast_admins(self, data: dict[str, Any]):
        """Send to all connected users (in this simple impl, broadcast to all)."""
        payload = json.dumps(data, ensure_ascii=False)
        dead: list[tuple[str, WebSocket]] = []
        for uid, conns in list(self._connections.items()):
            for ws in list(conns):
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append((uid, ws))
        for uid, ws in dead:
            self._connections.get(uid, set()).discard(ws)

    def count(self) -> int:
        return sum(len(v) for v in self._connections.values())


# Singleton manager — разделяется между всеми запросами
manager = ConnectionManager()


@router.websocket("/ws/notifications")
async def ws_notifications(websocket: WebSocket,
                            db: Session = Depends(get_db)):
    """
    WebSocket endpoint.
    Аутентификация через query-параметр ?token=<access_token>.
    """
    # Extract token from query params (FastAPI WebSocket query params
    # are not automatically injected as function arguments)
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    # Validate token
    token_record = TokenRepository(db).get_valid_token(token)
    if not token_record or not token_record.user:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    user = token_record.user
    if not user.is_active:
        await websocket.close(code=4003, reason="Account inactive")
        return

    await manager.connect(websocket, user.id)
    try:
        # Keep connection alive — ping every 25s
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=25)
            except asyncio.TimeoutError:
                await websocket.send_text(json.dumps({"type": "ping"}))
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, user.id)
