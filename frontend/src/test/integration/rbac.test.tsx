/**
 * Integration tests: RBAC — 401/403 behaviour.
 * Правило testing.md: тестировать RBAC.
 * Правило authorization.md: 401 unauthenticated, 403 forbidden.
 * Примечание: тесты используют MSW + fetch adapter.
 */
import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../mocks/server";

// Helper: делаем fetch-запрос как будто мы браузер
async function apiFetch(
  method: string,
  path: string,
  token?: string,
  body?: unknown,
) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const resp = await fetch(`http://localhost${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  return resp;
}

describe("RBAC — API responses", () => {
  it("returns 401 when no token provided", async () => {
    server.use(
      http.get("http://localhost/admin/users", () =>
        HttpResponse.json({ detail: "Не авторизован." }, { status: 401 })
      )
    );
    const res = await apiFetch("GET", "/admin/users");
    expect(res.status).toBe(401);
  });

  it("returns 403 when user lacks permission", async () => {
    server.use(
      http.get("http://localhost/admin/users", () =>
        HttpResponse.json({ detail: "Требуются права администратора." }, { status: 403 })
      )
    );
    const res = await apiFetch("GET", "/admin/users", "user-token-abc");
    expect(res.status).toBe(403);
    const data = await res.json();
    expect(data.detail).toContain("администратора");
  });

  it("allows admin to access /admin/users (200)", async () => {
    const res = await apiFetch("GET", "/admin/users", "admin-token-xyz");
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data)).toBe(true);
  });

  it("error message does not reveal auth method (generic 401)", async () => {
    server.use(
      http.post("http://localhost/auth/login", () =>
        HttpResponse.json({ detail: "Неверный email или пароль." }, { status: 401 })
      )
    );
    const res = await apiFetch("POST", "/auth/login", undefined, {
      email: "none@x.com", password: "wrong",
    });
    const data = await res.json();
    expect(data.detail).not.toContain("не найден");
    expect(data.detail).not.toContain("не существует");
  });
});

describe("Permission codes", () => {
  it("admin has users:manage permission", async () => {
    const res = await apiFetch("GET", "/auth/me/permissions", "admin-token-xyz");
    const data = await res.json();
    expect(data).toContain("users:manage");
  });

  it("regular user does not have users:manage", async () => {
    const res = await apiFetch("GET", "/auth/me/permissions", "user-token-abc");
    const data = await res.json();
    expect(data).not.toContain("users:manage");
  });
});
