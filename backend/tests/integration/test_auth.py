"""
Integration tests for authentication endpoints.

These tests use a real (SQLite in-memory) database via the `client` fixture.
"""
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def register_and_login(client, email="test@example.com", password="Password1"):
    client.post("/auth/register", json={
        "first_name": "Test",
        "last_name": "User",
        "middle_name": None,
        "email": email,
        "password": password,
        "password_repeat": password,
    })
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Registration ──────────────────────────────────────────────────────────────

class TestRegister:
    def test_success(self, client):
        resp = client.post("/auth/register", json={
            "first_name": "Alice",
            "last_name": "Smith",
            "middle_name": "B.",
            "email": "alice@example.com",
            "password": "Alice1234",
            "password_repeat": "Alice1234",
        })
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "alice@example.com"
        assert "password_hash" not in body

    def test_duplicate_email(self, client):
        payload = {
            "first_name": "Bob",
            "last_name": "Jones",
            "middle_name": None,
            "email": "bob@example.com",
            "password": "Bob12345",
            "password_repeat": "Bob12345",
        }
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 409

    def test_password_mismatch(self, client):
        resp = client.post("/auth/register", json={
            "first_name": "C",
            "last_name": "D",
            "email": "cd@example.com",
            "password": "Abc12345",
            "password_repeat": "Xyz12345",
        })
        assert resp.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    def test_success(self, client):
        client.post("/auth/register", json={
            "first_name": "E",
            "last_name": "F",
            "email": "ef@example.com",
            "password": "Pass1234",
            "password_repeat": "Pass1234",
        })
        resp = client.post("/auth/login", json={"email": "ef@example.com", "password": "Pass1234"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_wrong_password(self, client):
        client.post("/auth/register", json={
            "first_name": "G",
            "last_name": "H",
            "email": "gh@example.com",
            "password": "Pass1234",
            "password_repeat": "Pass1234",
        })
        resp = client.post("/auth/login", json={"email": "gh@example.com", "password": "WrongPass1"})
        assert resp.status_code == 401

    def test_nonexistent_user(self, client):
        resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "Pass1234"})
        assert resp.status_code == 401


# ── /auth/me ──────────────────────────────────────────────────────────────────

class TestMe:
    def test_authenticated(self, client):
        token = register_and_login(client)
        resp = client.get("/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@example.com"

    def test_no_token(self, client):
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_invalid_token(self, client):
        resp = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────

class TestLogout:
    def test_logout_invalidates_token(self, client):
        token = register_and_login(client, email="logout@example.com")
        resp = client.post("/auth/logout", headers=auth_headers(token))
        assert resp.status_code == 204
        # Token should now be invalid
        resp2 = client.get("/auth/me", headers=auth_headers(token))
        assert resp2.status_code == 401


# ── Update profile ────────────────────────────────────────────────────────────

class TestUpdateProfile:
    def test_update_name(self, client):
        token = register_and_login(client, email="update@example.com")
        resp = client.put(
            "/auth/profile",
            json={"first_name": "Updated", "last_name": "Name"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["first_name"] == "Updated"
        assert body["last_name"] == "Name"

    def test_unauthenticated(self, client):
        resp = client.put("/auth/profile", json={"first_name": "X"})
        assert resp.status_code == 401


# ── Soft delete ───────────────────────────────────────────────────────────────

class TestDeleteAccount:
    def test_soft_delete(self, client):
        token = register_and_login(client, email="delete@example.com")
        resp = client.delete("/auth/profile", headers=auth_headers(token))
        assert resp.status_code == 204

    def test_token_invalid_after_delete(self, client):
        token = register_and_login(client, email="delete2@example.com")
        client.delete("/auth/profile", headers=auth_headers(token))
        resp = client.get("/auth/me", headers=auth_headers(token))
        assert resp.status_code == 401

    def test_login_blocked_after_delete(self, client):
        register_and_login(client, email="delete3@example.com", password="Pass1234")
        # Get a fresh token first to confirm login works
        r1 = client.post("/auth/login", json={"email": "delete3@example.com", "password": "Pass1234"})
        token = r1.json()["access_token"]
        # Deactivate
        client.delete("/auth/profile", headers=auth_headers(token))
        # Login again should fail
        r2 = client.post("/auth/login", json={"email": "delete3@example.com", "password": "Pass1234"})
        assert r2.status_code == 403
