"""
Integration tests: Admin CRUD — roles, permissions, users, bulk ops.
Правило testing.md: тестировать RBAC и admin endpoints.
"""
import pytest

ADMIN   = {"email": "admin@example.com",   "password": "Admin1234!"}
MANAGER = {"email": "manager@example.com", "password": "Manager1234!"}
USER    = {"email": "user@example.com",    "password": "User1234!"}


def login(client, creds):
    r = client.post("/auth/login", json=creds)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def hdrs(token):
    return {"Authorization": f"Bearer {token}"}


# ── Roles CRUD ─────────────────────────────────────────────────────────────────

class TestRolesCRUD:
    def test_admin_can_list_roles(self, seeded_client):
        token = login(seeded_client, ADMIN)
        r = seeded_client.get("/admin/roles", headers=hdrs(token))
        assert r.status_code == 200
        names = [x["name"] for x in r.json()]
        assert "administrator" in names
        assert "user" in names

    def test_admin_can_create_role(self, seeded_client):
        token = login(seeded_client, ADMIN)
        r = seeded_client.post("/admin/roles",
            json={"name": "auditor", "description": "Аудитор"},
            headers=hdrs(token))
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "auditor"
        assert data["is_system"] is False

    def test_duplicate_role_name_409(self, seeded_client):
        token = login(seeded_client, ADMIN)
        seeded_client.post("/admin/roles",
            json={"name": "testrole"}, headers=hdrs(token))
        r = seeded_client.post("/admin/roles",
            json={"name": "testrole"}, headers=hdrs(token))
        assert r.status_code == 409

    def test_admin_can_update_role(self, seeded_client):
        token = login(seeded_client, ADMIN)
        created = seeded_client.post("/admin/roles",
            json={"name": "to_update"}, headers=hdrs(token)).json()
        r = seeded_client.put(f"/admin/roles/{created['id']}",
            json={"name": "updated_name", "description": "Новое описание"},
            headers=hdrs(token))
        assert r.status_code == 200
        assert r.json()["name"] == "updated_name"

    def test_admin_can_delete_non_system_role(self, seeded_client):
        token = login(seeded_client, ADMIN)
        created = seeded_client.post("/admin/roles",
            json={"name": "to_delete"}, headers=hdrs(token)).json()
        r = seeded_client.delete(f"/admin/roles/{created['id']}",
            headers=hdrs(token))
        assert r.status_code == 204

    def test_cannot_delete_system_role(self, seeded_client):
        token = login(seeded_client, ADMIN)
        roles = seeded_client.get("/admin/roles", headers=hdrs(token)).json()
        sys_role = next(r for r in roles if r["is_system"])
        r = seeded_client.delete(f"/admin/roles/{sys_role['id']}",
            headers=hdrs(token))
        assert r.status_code == 400

    def test_manager_cannot_manage_roles(self, seeded_client):
        token = login(seeded_client, MANAGER)
        r = seeded_client.post("/admin/roles",
            json={"name": "should_fail"}, headers=hdrs(token))
        assert r.status_code == 403

    def test_role_not_found_404(self, seeded_client):
        token = login(seeded_client, ADMIN)
        r = seeded_client.put("/admin/roles/nonexistent-id",
            json={"name": "x"}, headers=hdrs(token))
        assert r.status_code == 404


# ── Permissions CRUD ───────────────────────────────────────────────────────────

class TestPermissionsCRUD:
    def test_admin_can_list_permissions(self, seeded_client):
        token = login(seeded_client, ADMIN)
        r = seeded_client.get("/admin/permissions", headers=hdrs(token))
        assert r.status_code == 200
        codes = [p["code"] for p in r.json()]
        assert "reports:read" in codes
        assert "users:manage" in codes

    def test_admin_can_create_permission(self, seeded_client):
        token = login(seeded_client, ADMIN)
        r = seeded_client.post("/admin/permissions", json={
            "code": "invoices:read",
            "resource": "invoices",
            "action": "read",
            "description": "Просмотр счетов",
        }, headers=hdrs(token))
        assert r.status_code == 201
        assert r.json()["code"] == "invoices:read"

    def test_duplicate_permission_code_409(self, seeded_client):
        token = login(seeded_client, ADMIN)
        seeded_client.post("/admin/permissions", json={
            "code": "test:dup", "resource": "test", "action": "dup"
        }, headers=hdrs(token))
        r = seeded_client.post("/admin/permissions", json={
            "code": "test:dup", "resource": "test", "action": "dup"
        }, headers=hdrs(token))
        assert r.status_code == 409

    def test_admin_can_update_permission_description(self, seeded_client):
        token = login(seeded_client, ADMIN)
        created = seeded_client.post("/admin/permissions", json={
            "code": "test:update", "resource": "test", "action": "update"
        }, headers=hdrs(token)).json()
        r = seeded_client.put(f"/admin/permissions/{created['id']}",
            json={"description": "Обновлённое описание"},
            headers=hdrs(token))
        assert r.status_code == 200
        assert r.json()["description"] == "Обновлённое описание"

    def test_admin_can_delete_permission(self, seeded_client):
        token = login(seeded_client, ADMIN)
        created = seeded_client.post("/admin/permissions", json={
            "code": "test:delete_me", "resource": "test", "action": "delete_me"
        }, headers=hdrs(token)).json()
        r = seeded_client.delete(f"/admin/permissions/{created['id']}",
            headers=hdrs(token))
        assert r.status_code == 204


# ── Role ↔ Permission assignment ──────────────────────────────────────────────

class TestRolePermissionAssignment:
    def test_admin_can_get_role_permissions(self, seeded_client):
        token = login(seeded_client, ADMIN)
        roles = seeded_client.get("/admin/roles", headers=hdrs(token)).json()
        mgr_role = next(r for r in roles if r["name"] == "manager")
        r = seeded_client.get(f"/admin/roles/{mgr_role['id']}/permissions",
            headers=hdrs(token))
        assert r.status_code == 200
        codes = [p["code"] for p in r.json()]
        assert "reports:read" in codes

    def test_admin_can_assign_permissions_to_role(self, seeded_client):
        token = login(seeded_client, ADMIN)
        # Создаём роль
        role = seeded_client.post("/admin/roles",
            json={"name": "test_assign_role"}, headers=hdrs(token)).json()
        # Берём разрешение
        perms = seeded_client.get("/admin/permissions", headers=hdrs(token)).json()
        perm_ids = [perms[0]["id"]]
        # Назначаем
        r = seeded_client.post(f"/admin/roles/{role['id']}/permissions",
            json={"permission_ids": perm_ids}, headers=hdrs(token))
        assert r.status_code == 204
        # Проверяем
        r2 = seeded_client.get(f"/admin/roles/{role['id']}/permissions",
            headers=hdrs(token))
        assert len(r2.json()) == 1


# ── User management ───────────────────────────────────────────────────────────

class TestAdminUserManagement:
    def test_admin_can_list_users(self, seeded_client):
        token = login(seeded_client, ADMIN)
        r = seeded_client.get("/admin/users", headers=hdrs(token))
        assert r.status_code == 200
        assert len(r.json()) >= 3

    def test_admin_can_filter_users_by_active(self, seeded_client):
        token = login(seeded_client, ADMIN)
        r = seeded_client.get("/admin/users?is_active=true", headers=hdrs(token))
        assert r.status_code == 200
        for u in r.json():
            assert u["is_active"] is True

    def test_admin_can_search_users(self, seeded_client):
        token = login(seeded_client, ADMIN)
        r = seeded_client.get("/admin/users?search=admin", headers=hdrs(token))
        assert r.status_code == 200
        assert any("admin" in u["email"] for u in r.json())

    def test_admin_can_get_user_by_id(self, seeded_client):
        token = login(seeded_client, ADMIN)
        users = seeded_client.get("/admin/users", headers=hdrs(token)).json()
        user_id = users[0]["id"]
        r = seeded_client.get(f"/admin/users/{user_id}", headers=hdrs(token))
        assert r.status_code == 200
        assert r.json()["id"] == user_id

    def test_admin_can_update_user_profile(self, seeded_client):
        token = login(seeded_client, ADMIN)
        users = seeded_client.get("/admin/users", headers=hdrs(token)).json()
        user_id = next(u["id"] for u in users if u["email"] == USER["email"])
        r = seeded_client.put(f"/admin/users/{user_id}",
            json={"first_name": "UpdatedFirst", "last_name": "UpdatedLast"},
            headers=hdrs(token))
        assert r.status_code == 200
        assert r.json()["first_name"] == "UpdatedFirst"

    def test_admin_can_deactivate_user(self, seeded_client):
        token = login(seeded_client, ADMIN)
        users = seeded_client.get("/admin/users", headers=hdrs(token)).json()
        user_id = next(u["id"] for u in users if u["email"] == USER["email"])
        r = seeded_client.patch(f"/admin/users/{user_id}/deactivate",
            headers=hdrs(token))
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_admin_can_activate_user(self, seeded_client):
        token = login(seeded_client, ADMIN)
        users = seeded_client.get("/admin/users", headers=hdrs(token)).json()
        user_id = next(u["id"] for u in users if u["email"] == USER["email"])
        # Сначала деактивируем
        seeded_client.patch(f"/admin/users/{user_id}/deactivate", headers=hdrs(token))
        # Затем активируем
        r = seeded_client.patch(f"/admin/users/{user_id}/activate", headers=hdrs(token))
        assert r.status_code == 200
        assert r.json()["is_active"] is True

    def test_admin_can_set_user_password(self, seeded_client):
        token = login(seeded_client, ADMIN)
        users = seeded_client.get("/admin/users", headers=hdrs(token)).json()
        user_id = next(u["id"] for u in users if u["email"] == MANAGER["email"])
        r = seeded_client.post(f"/admin/users/{user_id}/set-password",
            json={"new_password": "NewManager1234!"},
            headers=hdrs(token))
        assert r.status_code == 204
        # Убеждаемся что новый пароль работает
        r2 = seeded_client.post("/auth/login",
            json={"email": MANAGER["email"], "password": "NewManager1234!"})
        assert r2.status_code == 200

    def test_admin_can_logout_all_sessions(self, seeded_client):
        # Создаём несколько сессий
        t1 = login(seeded_client, USER)
        t2 = login(seeded_client, USER)
        # Получаем user_id
        user_id = seeded_client.get("/auth/me", headers=hdrs(t1)).json()["id"]
        # Admin отзывает все сессии
        admin_token = login(seeded_client, ADMIN)
        r = seeded_client.post(f"/admin/users/{user_id}/logout-all",
            headers=hdrs(admin_token))
        assert r.status_code == 204
        # Оба токена должны стать невалидны
        assert seeded_client.get("/auth/me", headers=hdrs(t1)).status_code == 401
        assert seeded_client.get("/auth/me", headers=hdrs(t2)).status_code == 401

    def test_admin_cannot_delete_self(self, seeded_client):
        token = login(seeded_client, ADMIN)
        me = seeded_client.get("/auth/me", headers=hdrs(token)).json()
        r = seeded_client.delete(f"/admin/users/{me['id']}", headers=hdrs(token))
        assert r.status_code == 400

    def test_user_export_csv(self, seeded_client):
        token = login(seeded_client, ADMIN)
        r = seeded_client.get("/admin/users/export/csv", headers=hdrs(token))
        assert r.status_code == 200
        assert "text/csv" in r.headers.get("content-type", "")
        lines = r.text.strip().split("\n")
        assert len(lines) >= 2  # header + at least 1 user
        assert "email" in lines[0]


# ── Bulk operations ────────────────────────────────────────────────────────────

class TestBulkOperations:
    def _get_user_ids(self, seeded_client, admin_token, emails):
        users = seeded_client.get("/admin/users", headers=hdrs(admin_token)).json()
        return [u["id"] for u in users if u["email"] in emails]

    def test_bulk_deactivate(self, seeded_client):
        token = login(seeded_client, ADMIN)
        ids = self._get_user_ids(seeded_client, token,
            {MANAGER["email"], USER["email"]})
        r = seeded_client.post("/admin/users/bulk/deactivate",
            json={"user_ids": ids}, headers=hdrs(token))
        assert r.status_code == 200
        assert r.json()["updated"] == 2

    def test_bulk_activate(self, seeded_client):
        token = login(seeded_client, ADMIN)
        ids = self._get_user_ids(seeded_client, token,
            {MANAGER["email"], USER["email"]})
        # Сначала деактивируем
        seeded_client.post("/admin/users/bulk/deactivate",
            json={"user_ids": ids}, headers=hdrs(token))
        # Активируем
        r = seeded_client.post("/admin/users/bulk/activate",
            json={"user_ids": ids}, headers=hdrs(token))
        assert r.status_code == 200
        assert r.json()["updated"] == 2

    def test_bulk_assign_role(self, seeded_client):
        token = login(seeded_client, ADMIN)
        ids = self._get_user_ids(seeded_client, token, {USER["email"]})
        roles = seeded_client.get("/admin/roles", headers=hdrs(token)).json()
        mgr_role_id = next(r["id"] for r in roles if r["name"] == "manager")
        r = seeded_client.post("/admin/users/bulk/assign-role", json={
            "user_ids": ids,
            "role_id": mgr_role_id,
        }, headers=hdrs(token))
        assert r.status_code == 200
        assert r.json()["updated"] >= 1

    def test_bulk_deactivate_skips_admin(self, seeded_client):
        """Admin не должен самодеактивироваться через bulk."""
        token = login(seeded_client, ADMIN)
        me = seeded_client.get("/auth/me", headers=hdrs(token)).json()
        r = seeded_client.post("/admin/users/bulk/deactivate",
            json={"user_ids": [me["id"]]}, headers=hdrs(token))
        assert r.status_code == 200
        # Admin пропускается — updated = 0
        assert r.json()["updated"] == 0
