/**
 * MSW handlers for tests (Node.js / jsdom environment).
 * Правило testing.md: mock all external API calls.
 */
import { http, HttpResponse } from "msw";

// В Node/jsdom MSW перехватывает fetch через полный URL
const BASE = "http://localhost";

export const mockUser = {
  id: "user-uuid-1", first_name: "Иван", last_name: "Петров",
  middle_name: null, email: "ivan@example.com", recovery_email: null,
  is_active: true, avatar_url: null, last_login_at: null,
  created_at: "2026-06-01T10:00:00Z", updated_at: "2026-06-01T10:00:00Z",
};

export const mockAdminUser = {
  ...mockUser, id: "admin-uuid-1",
  email: "admin@example.com", first_name: "Admin",
};

export const mockToken = {
  access_token: "test-token-abc123", token_type: "bearer",
  expires_at: new Date(Date.now() + 86400000).toISOString(),
};

export const mockRoles = [
  { id: "role-1", name: "administrator", description: "Полный доступ", is_system: true },
  { id: "role-2", name: "manager",       description: "Менеджер",      is_system: false },
  { id: "role-3", name: "user",          description: "Пользователь",  is_system: false },
];

export const mockPermissions = [
  { id: "perm-1", code: "users:read",   resource: "users",   action: "read",   description: null },
  { id: "perm-2", code: "users:manage", resource: "users",   action: "manage", description: null },
  { id: "perm-3", code: "reports:read", resource: "reports", action: "read",   description: null },
];

export const handlers = [
  // ── Auth ───────────────────────────────────────────────────────────────────
  http.post(`${BASE}/auth/login`, async ({ request }) => {
    const body = await request.json() as { email: string; password: string };
    if (body.email === "admin@example.com" && body.password === "Admin1234!") {
      return HttpResponse.json({ ...mockToken, access_token: "admin-token-xyz" });
    }
    if (body.email === "ivan@example.com" && body.password === "Pass1234") {
      return HttpResponse.json({ ...mockToken, access_token: "user-token-abc" });
    }
    return HttpResponse.json({ detail: "Неверный email или пароль." }, { status: 401 });
  }),

  http.post(`${BASE}/auth/register`, async ({ request }) => {
    const body = await request.json() as Record<string, string>;
    if (body.email === "existing@example.com") {
      return HttpResponse.json({ detail: "Email уже зарегистрирован." }, { status: 409 });
    }
    return HttpResponse.json({ ...mockUser, email: body.email }, { status: 201 });
  }),

  http.post(`${BASE}/auth/logout`,          () => new HttpResponse(null, { status: 204 })),
  http.post(`${BASE}/auth/forgot-password`, () => new HttpResponse(null, { status: 204 })),
  http.post(`${BASE}/auth/reset-password`,  () => new HttpResponse(null, { status: 204 })),
  http.delete(`${BASE}/auth/profile`,       () => new HttpResponse(null, { status: 204 })),

  http.get(`${BASE}/auth/me`, ({ request }) => {
    const auth = request.headers.get("Authorization") ?? "";
    if (!auth.startsWith("Bearer "))
      return HttpResponse.json({ detail: "Unauthorized" }, { status: 401 });
    return HttpResponse.json(auth.includes("admin") ? mockAdminUser : mockUser);
  }),

  http.get(`${BASE}/auth/me/roles`, ({ request }) => {
    const auth = request.headers.get("Authorization") ?? "";
    return HttpResponse.json(auth.includes("admin") ? [mockRoles[0]] : [mockRoles[2]]);
  }),

  http.get(`${BASE}/auth/me/permissions`, ({ request }) => {
    const auth = request.headers.get("Authorization") ?? "";
    if (auth.includes("admin")) return HttpResponse.json(mockPermissions.map(p => p.code));
    return HttpResponse.json(["reports:read", "documents:read", "settings:read"]);
  }),

  http.put(`${BASE}/auth/profile`, async ({ request }) => {
    const body = await request.json() as Record<string, string>;
    return HttpResponse.json({ ...mockUser, ...body });
  }),

  http.get(`${BASE}/auth/me/sessions`,     () => HttpResponse.json([])),
  http.get(`${BASE}/auth/public/roles`,    () => HttpResponse.json([mockRoles[1], mockRoles[2]])),
  http.get(`${BASE}/auth/password-policy`, () => HttpResponse.json({
    min_length: 8, require_digit: true, require_letter: true,
    require_upper: false, require_special: false, expire_days: 0,
  })),
  http.get(`${BASE}/auth/2fa/status`, () => HttpResponse.json({ enabled: false })),

  // ── Admin ──────────────────────────────────────────────────────────────────
  http.get(`${BASE}/admin/users`,         () => HttpResponse.json([mockUser, mockAdminUser])),
  http.get(`${BASE}/admin/roles`,         () => HttpResponse.json(mockRoles)),
  http.get(`${BASE}/admin/permissions`,   () => HttpResponse.json(mockPermissions)),
  http.get(`${BASE}/admin/notifications`, () => HttpResponse.json([])),
  http.get(`${BASE}/admin/notifications/unread-count`, () => HttpResponse.json({ count: 0 })),
  http.get(`${BASE}/admin/audit-log`,     () => HttpResponse.json([])),
  http.get(`${BASE}/admin/policy`,        () => HttpResponse.json({
    min_length: 8, require_digit: true, require_letter: true,
    require_upper: false, require_special: false, expire_days: 0,
  })),
  http.patch(`${BASE}/admin/notifications/:id/read`,
    () => new HttpResponse(null, { status: 204 })
  ),
  http.patch(`${BASE}/admin/notifications/read-all`,
    () => new HttpResponse(null, { status: 204 })
  ),

  http.get(`${BASE}/admin/users/:id/roles`, ({ params }) =>
    HttpResponse.json({ user_id: params.id, roles: [mockRoles[2]] })
  ),
  http.post(`${BASE}/admin/users/:id/roles`, ({ params }) =>
    HttpResponse.json({ user_id: params.id, roles: [mockRoles[1]] })
  ),
  http.post(`${BASE}/admin/roles`, async ({ request }) => {
    const body = await request.json() as Record<string, string>;
    return HttpResponse.json({ id: "new-role-id", ...body, is_system: false }, { status: 201 });
  }),
  http.delete(`${BASE}/admin/roles/:id`,       () => new HttpResponse(null, { status: 204 })),
  http.post(`${BASE}/admin/permissions`, async ({ request }) => {
    const body = await request.json() as Record<string, string>;
    return HttpResponse.json({ id: "new-perm-id", ...body }, { status: 201 });
  }),
  http.patch(`${BASE}/admin/users/:id/activate`,
    ({ params }) => HttpResponse.json({ ...mockUser, id: params.id as string, is_active: true })
  ),
  http.patch(`${BASE}/admin/users/:id/deactivate`,
    ({ params }) => HttpResponse.json({ ...mockUser, id: params.id as string, is_active: false })
  ),

  // ── Resources ──────────────────────────────────────────────────────────────
  http.get(`${BASE}/reports`,   () => HttpResponse.json([])),
  http.get(`${BASE}/documents`, () => HttpResponse.json([])),
  http.get(`${BASE}/settings`,  () => HttpResponse.json({
    site_name: "Auth Manager", maintenance_mode: false, max_upload_size_mb: 10,
  })),
];
