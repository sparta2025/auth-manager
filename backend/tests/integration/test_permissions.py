"""
Integration tests for the permission system.

Uses the `seeded_client` fixture so all three test users + roles +
permissions are pre-loaded.
"""
import pytest

ADMIN    = {"email": "admin@example.com",   "password": "Admin1234!"}
MANAGER  = {"email": "manager@example.com", "password": "Manager1234!"}
USER     = {"email": "user@example.com",    "password": "User1234!"}


def login(client, creds: dict) -> str:
    resp = client.post("/auth/login", json=creds)
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    return resp.json()["access_token"]


def hdrs(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── 401 checks ────────────────────────────────────────────────────────────────

class Test401:
    def test_reports_no_auth(self, seeded_client):
        resp = seeded_client.get("/reports")
        assert resp.status_code == 401

    def test_admin_no_auth(self, seeded_client):
        resp = seeded_client.get("/admin/roles")
        assert resp.status_code == 401


# ── 403 checks ────────────────────────────────────────────────────────────────

class Test403:
    def test_user_cannot_access_admin(self, seeded_client):
        token = login(seeded_client, USER)
        resp = seeded_client.get("/admin/roles", headers=hdrs(token))
        assert resp.status_code == 403

    def test_manager_cannot_access_admin(self, seeded_client):
        token = login(seeded_client, MANAGER)
        resp = seeded_client.get("/admin/roles", headers=hdrs(token))
        assert resp.status_code == 403

    def test_user_cannot_delete_report(self, seeded_client):
        # Create a report as manager
        mgr_token = login(seeded_client, MANAGER)
        create = seeded_client.post(
            "/reports",
            json={"title": "Test", "content": "Body"},
            headers=hdrs(mgr_token),
        )
        report_id = create.json()["id"]
        # Try to delete as user (no delete permission)
        usr_token = login(seeded_client, USER)
        resp = seeded_client.delete(f"/reports/{report_id}", headers=hdrs(usr_token))
        assert resp.status_code == 403

    def test_user_cannot_update_settings(self, seeded_client):
        token = login(seeded_client, USER)
        resp = seeded_client.put("/settings", json={"site_name": "Hacked"}, headers=hdrs(token))
        assert resp.status_code == 403


# ── Role checks ───────────────────────────────────────────────────────────────

class TestRoles:
    def test_admin_can_list_roles(self, seeded_client):
        token = login(seeded_client, ADMIN)
        resp = seeded_client.get("/admin/roles", headers=hdrs(token))
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()]
        assert "administrator" in names

    def test_admin_can_create_role(self, seeded_client):
        token = login(seeded_client, ADMIN)
        resp = seeded_client.post(
            "/admin/roles",
            json={"name": "auditor", "description": "Read-only audit access"},
            headers=hdrs(token),
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "auditor"

    def test_admin_can_assign_roles(self, seeded_client):
        adm_token = login(seeded_client, ADMIN)
        # Get manager user ID
        mgr_resp = seeded_client.post("/auth/login", json=MANAGER)
        mgr_token = mgr_resp.json()["access_token"]
        me_resp = seeded_client.get("/auth/me", headers=hdrs(mgr_token))
        mgr_id = me_resp.json()["id"]
        # Get role IDs
        roles = seeded_client.get("/admin/roles", headers=hdrs(adm_token)).json()
        user_role_id = next(r["id"] for r in roles if r["name"] == "user")
        # Assign
        resp = seeded_client.post(
            f"/admin/users/{mgr_id}/roles",
            json={"role_ids": [user_role_id]},
            headers=hdrs(adm_token),
        )
        assert resp.status_code == 200


# ── Resource permission checks ────────────────────────────────────────────────

class TestResourcePermissions:
    def test_user_can_read_reports(self, seeded_client):
        token = login(seeded_client, USER)
        resp = seeded_client.get("/reports", headers=hdrs(token))
        assert resp.status_code == 200

    def test_manager_can_create_report(self, seeded_client):
        token = login(seeded_client, MANAGER)
        resp = seeded_client.post(
            "/reports",
            json={"title": "Q1", "content": "Numbers"},
            headers=hdrs(token),
        )
        assert resp.status_code == 201

    def test_admin_can_read_settings(self, seeded_client):
        token = login(seeded_client, ADMIN)
        resp = seeded_client.get("/settings", headers=hdrs(token))
        assert resp.status_code == 200

    def test_admin_can_update_settings(self, seeded_client):
        token = login(seeded_client, ADMIN)
        resp = seeded_client.put(
            "/settings",
            json={"site_name": "New Name"},
            headers=hdrs(token),
        )
        assert resp.status_code == 200
        assert resp.json()["site_name"] == "New Name"

    def test_user_can_read_documents(self, seeded_client):
        token = login(seeded_client, USER)
        resp = seeded_client.get("/documents", headers=hdrs(token))
        assert resp.status_code == 200

    def test_user_cannot_create_document(self, seeded_client):
        token = login(seeded_client, USER)
        resp = seeded_client.post(
            "/documents",
            json={"name": "Secret", "body": "content"},
            headers=hdrs(token),
        )
        assert resp.status_code == 403
