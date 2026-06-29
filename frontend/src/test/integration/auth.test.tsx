/**
 * Integration tests: Login and Register API flows.
 * Правило testing.md: тестировать auth flows.
 */
import { describe, it, expect } from "vitest";

const BASE = "http://localhost";

async function postJSON(path: string, body: unknown) {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return { status: res.status, data: await res.json() };
}

describe("Login flow", () => {
  it("returns token on valid admin credentials", async () => {
    const { status, data } = await postJSON("/auth/login", {
      email: "admin@example.com",
      password: "Admin1234!",
    });
    expect(status).toBe(200);
    expect(data.access_token).toBe("admin-token-xyz");
    expect(data.token_type).toBe("bearer");
  });

  it("returns token on valid user credentials", async () => {
    const { status, data } = await postJSON("/auth/login", {
      email: "ivan@example.com",
      password: "Pass1234",
    });
    expect(status).toBe(200);
    expect(data.access_token).toBe("user-token-abc");
  });

  it("returns 401 on wrong password", async () => {
    const { status, data } = await postJSON("/auth/login", {
      email: "admin@example.com",
      password: "wrongpassword",
    });
    expect(status).toBe(401);
    expect(data.detail).toContain("Неверный email");
  });

  it("returns 401 on non-existent email", async () => {
    const { status } = await postJSON("/auth/login", {
      email: "nobody@example.com",
      password: "SomePass1",
    });
    expect(status).toBe(401);
  });

  it("does not reveal whether user exists (generic error)", async () => {
    const { data } = await postJSON("/auth/login", {
      email: "nobody@example.com",
      password: "SomePass1",
    });
    // OWASP A07: не раскрываем детали
    expect(data.detail).not.toMatch(/не найден|не существует|not found/i);
  });
});

describe("Register flow", () => {
  it("returns 201 on new user registration", async () => {
    const { status, data } = await postJSON("/auth/register", {
      first_name: "Test", last_name: "User",
      email: "newuser@example.com",
      password: "Pass1234", password_repeat: "Pass1234",
    });
    expect(status).toBe(201);
    expect(data.email).toBe("newuser@example.com");
    expect(data).not.toHaveProperty("password_hash");
  });

  it("returns 409 on duplicate email", async () => {
    const { status, data } = await postJSON("/auth/register", {
      first_name: "Test", last_name: "User",
      email: "existing@example.com",
      password: "Pass1234", password_repeat: "Pass1234",
    });
    expect(status).toBe(409);
    expect(data.detail).toContain("уже зарегистрирован");
  });
});

describe("Forgot password flow", () => {
  it("returns 204 regardless of email existence (OWASP A07)", async () => {
    // Всегда возвращаем 204 — не раскрываем существование email
    const res = await fetch(`${BASE}/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: "anyone@example.com" }),
    });
    expect(res.status).toBe(204);
  });
});
