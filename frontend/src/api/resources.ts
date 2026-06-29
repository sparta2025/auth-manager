import { apiClient } from "./client";
import type { Document, Report, Settings } from "../types";
export const reportsApi = {
  getAll: () => apiClient.get<Report[]>("/reports").then(r=>r.data),
  create: (d: object) => apiClient.post<Report>("/reports", d).then(r=>r.data),
  update: (id: string, d: object) => apiClient.put<Report>(`/reports/${id}`, d).then(r=>r.data),
  delete: (id: string) => apiClient.delete(`/reports/${id}`),
};
export const documentsApi = {
  getAll: () => apiClient.get<Document[]>("/documents").then(r=>r.data),
  create: (d: object) => apiClient.post<Document>("/documents", d).then(r=>r.data),
  update: (id: string, d: object) => apiClient.put<Document>(`/documents/${id}`, d).then(r=>r.data),
  delete: (id: string) => apiClient.delete(`/documents/${id}`),
};
export const settingsApi = {
  get: () => apiClient.get<Settings>("/settings").then(r=>r.data),
  update: (d: object) => apiClient.put<Settings>("/settings", d).then(r=>r.data),
};
