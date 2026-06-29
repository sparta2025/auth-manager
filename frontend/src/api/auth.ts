import { apiClient } from "./client";
import type { Role, SessionInfo, TokenResponse, User } from "../types";
export const authApi = {
  login: (email: string, password: string) => apiClient.post<TokenResponse>("/auth/login", {email, password}).then(r=>r.data),
  register: (d: object) => apiClient.post<User>("/auth/register", d).then(r=>r.data),
  logout: () => apiClient.post("/auth/logout"),
  me: () => apiClient.get<User>("/auth/me").then(r=>r.data),
  myRoles: () => apiClient.get<Role[]>("/auth/me/roles").then(r=>r.data),
  myPermissions: () => apiClient.get<string[]>("/auth/me/permissions").then(r=>r.data),
  updateProfile: (d: object) => apiClient.put<User>("/auth/profile", d).then(r=>r.data),
  changePassword: (d: object) => apiClient.post("/auth/change-password", d),
  forgotPassword: (email: string) => apiClient.post("/auth/forgot-password", {email}),
  resetPassword: (d: object) => apiClient.post("/auth/reset-password", d),
  deleteAccount: () => apiClient.delete("/auth/profile"),
  mySessions: () => apiClient.get<SessionInfo[]>("/auth/me/sessions").then(r=>r.data),
  revokeSession: (id: string) => apiClient.delete(`/auth/me/sessions/${id}`),
  publicRoles: () => apiClient.get<Role[]>("/auth/public/roles").then(r=>r.data),
};
