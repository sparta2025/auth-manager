import axios, { AxiosError } from "axios";
const BASE_URL = import.meta.env.VITE_API_URL ?? "";
export const apiClient = axios.create({ baseURL: BASE_URL, headers: { "Content-Type": "application/json" } });
apiClient.interceptors.request.use((c) => {
  const t = localStorage.getItem("access_token");
  if (t) c.headers.Authorization = `Bearer ${t}`;
  return c;
});
apiClient.interceptors.response.use((r) => r, (error: AxiosError) => {
  if (error.response?.status === 401 && !window.location.pathname.includes("/login") && !window.location.pathname.includes("/reset-password") && !window.location.pathname.includes("/forgot-password")) {
    localStorage.removeItem("access_token");
    window.location.href = "/login";
  }
  return Promise.reject(error);
});
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const d = error.response?.data;
    if (typeof d?.detail === "string") return d.detail;
    if (Array.isArray(d?.detail)) return d.detail.map((x: {msg:string}) => x.msg).join("; ");
    return error.message;
  }
  return "Неизвестная ошибка";
}
