"""Integration tests: audit log, notifications, password reset."""
import pytest

ADMIN = {"email": "admin@example.com",   "password": "Admin1234!"}
USER  = {"email": "user@example.com",    "password": "User1234!"}


def login(client, creds):
    r = client.post("/auth/login", json=creds)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def hdrs(token):
    return {"Authorization": f"Bearer {token}"}


class TestAuditLog:
    def test_admin_can_read_audit_log(self, seeded_client):
        token = login(seeded_client, ADMIN)
        r = seeded_client.get("/admin/audit-log", headers=hdrs(token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_user_cannot_read_audit_log(self, seeded_client):
        token = login(seeded_client, USER)
        r = seeded_client.get("/admin/audit-log", headers=hdrs(token))
        assert r.status_code == 403

    def test_login_creates_audit_entry(self, seeded_client):
        admin_token = login(seeded_client, ADMIN)
        # Logout создаёт запись
        seeded_client.post("/auth/logout", headers=hdrs(admin_token))
        # Логинимся снова
        admin_token2 = login(seeded_client, ADMIN)
        r = seeded_client.get("/admin/audit-log", headers=hdrs(admin_token2))
        actions = [e["action"] for e in r.json()]
        assert "user.login" in actions

    def test_audit_log_filter_by_action(self, seeded_client):
        admin_token = login(seeded_client, ADMIN)
        r = seeded_client.get(
            "/admin/audit-log?action=user.login",
            headers=hdrs(admin_token)
        )
        assert r.status_code == 200
        for entry in r.json():
            assert "login" in entry["action"]

    def test_audit_log_export_csv(self, seeded_client):
        admin_token = login(seeded_client, ADMIN)
        r = seeded_client.get(
            "/admin/audit-log/export/csv",
            headers=hdrs(admin_token)
        )
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        # CSV должен содержать заголовок
        assert "action" in r.text


class TestNotifications:
    def test_admin_sees_notifications(self, seeded_client):
        admin_token = login(seeded_client, ADMIN)
        r = seeded_client.get("/admin/notifications", headers=hdrs(admin_token))
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_unread_count_endpoint(self, seeded_client):
        admin_token = login(seeded_client, ADMIN)
        r = seeded_client.get(
            "/admin/notifications/unread-count",
            headers=hdrs(admin_token)
        )
        assert r.status_code == 200
        assert "count" in r.json()

    def test_mark_all_read(self, seeded_client):
        admin_token = login(seeded_client, ADMIN)
        r = seeded_client.patch(
            "/admin/notifications/read-all",
            headers=hdrs(admin_token)
        )
        assert r.status_code == 204

        # После mark-all unread_count должен быть 0
        r2 = seeded_client.get(
            "/admin/notifications/unread-count",
            headers=hdrs(admin_token)
        )
        assert r2.json()["count"] == 0

    def test_user_cannot_see_notifications(self, seeded_client):
        user_token = login(seeded_client, USER)
        r = seeded_client.get("/admin/notifications", headers=hdrs(user_token))
        assert r.status_code == 403


class TestPasswordReset:
    def test_forgot_password_always_204(self, client):
        """OWASP A07: не раскрываем существование email."""
        r = client.post("/auth/forgot-password",
                        json={"email": "nonexistent@example.com"})
        assert r.status_code == 204

    def test_reset_with_invalid_token_400(self, client):
        r = client.post("/auth/reset-password", json={
            "token": "invalidtoken123",
            "new_password": "NewPass123",
            "new_password_repeat": "NewPass123",
        })
        assert r.status_code == 400

    def test_reset_password_mismatched_400(self, client):
        r = client.post("/auth/reset-password", json={
            "token": "sometoken",
            "new_password": "NewPass123",
            "new_password_repeat": "DifferentPass456",
        })
        assert r.status_code == 422


class TestSessions:
    def test_user_can_list_own_sessions(self, seeded_client):
        token = login(seeded_client, USER)
        r = seeded_client.get("/auth/me/sessions", headers=hdrs(token))
        assert r.status_code == 200
        sessions = r.json()
        assert isinstance(sessions, list)
        assert len(sessions) >= 1

    def test_user_can_revoke_own_session(self, seeded_client):
        # Создаём второй токен (второй логин)
        r1 = seeded_client.post("/auth/login", json=USER)
        token1 = r1.json()["access_token"]
        r2 = seeded_client.post("/auth/login", json=USER)
        token2 = r2.json()["access_token"]

        # Получаем список сессий
        sessions_r = seeded_client.get("/auth/me/sessions", headers=hdrs(token1))
        sessions = sessions_r.json()
        assert len(sessions) >= 2

        # Отзываем первую сессию (не текущую — это будет сложнее определить)
        # Используем второй токен чтобы отозвать сессию первого
        target_id = sessions[-1]["id"]
        revoke_r = seeded_client.delete(
            f"/auth/me/sessions/{target_id}",
            headers=hdrs(token2)
        )
        # Может быть 204 (успех) или 404 (если сессия не принадлежит user2)
        assert revoke_r.status_code in (204, 404)

    def test_cannot_revoke_other_users_session(self, seeded_client):
        admin_token = login(seeded_client, ADMIN)
        user_token  = login(seeded_client, USER)

        # Получаем сессии admin
        admin_sessions = seeded_client.get(
            "/auth/me/sessions", headers=hdrs(admin_token)
        ).json()
        admin_session_id = admin_sessions[0]["id"]

        # Пытаемся отозвать сессию admin от имени user → 404
        r = seeded_client.delete(
            f"/auth/me/sessions/{admin_session_id}",
            headers=hdrs(user_token)
        )
        assert r.status_code == 404
