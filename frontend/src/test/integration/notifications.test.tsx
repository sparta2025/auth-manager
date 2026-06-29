/**
 * Integration tests: Admin notifications.
 */
import { describe, it, expect } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../mocks/server";

async function apiFetch(method: string, path: string, token = "admin-token-xyz") {
  return fetch(`http://localhost${path}`, {
    method,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
    },
  });
}

describe("Notifications", () => {
  it("returns empty notifications list by default", async () => {
    const res  = await apiFetch("GET", "/admin/notifications");
    expect(res.status).toBe(200);
    const data = await res.json();
    expect(Array.isArray(data)).toBe(true);
    expect(data).toHaveLength(0);
  });

  it("returns unread count of 3", async () => {
    server.use(
      http.get("http://localhost/admin/notifications/unread-count", () =>
        HttpResponse.json({ count: 3 })
      )
    );
    const res  = await apiFetch("GET", "/admin/notifications/unread-count");
    const data = await res.json();
    expect(data.count).toBe(3);
  });

  it("marks notification as read (204)", async () => {
    server.use(
      http.patch("http://localhost/admin/notifications/notif-1/read", () =>
        new HttpResponse(null, { status: 204 })
      )
    );
    const res = await apiFetch("PATCH", "/admin/notifications/notif-1/read");
    expect(res.status).toBe(204);
  });

  it("marks all notifications as read", async () => {
    server.use(
      http.patch("http://localhost/admin/notifications/read-all", () =>
        new HttpResponse(null, { status: 204 })
      )
    );
    const res = await apiFetch("PATCH", "/admin/notifications/read-all");
    expect(res.status).toBe(204);
  });
});
