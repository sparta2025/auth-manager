/**
 * Silent token refresh — за 5 минут до истечения токена
 * автоматически вызывает POST /auth/refresh.
 */
import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { apiClient } from "../api/client";
import type { TokenResponse } from "../types";

const REFRESH_BEFORE_MS = 5 * 60 * 1000;

function getExpiresAt(): number | null {
  const raw = localStorage.getItem("token_expires_at");
  if (!raw) return null;
  const ts = parseInt(raw, 10);
  return isNaN(ts) ? null : ts;
}

export function useTokenRefresh() {
  const navigate = useNavigate();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const doRefresh = async () => {
    try {
      const { data } = await apiClient.post<TokenResponse>("/auth/refresh");
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("token_expires_at",
        String(new Date(data.expires_at).getTime()));
      scheduleRefresh();
    } catch {
      localStorage.removeItem("access_token");
      localStorage.removeItem("token_expires_at");
      navigate("/login");
    }
  };

  const scheduleRefresh = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    const expiresAt = getExpiresAt();
    if (!expiresAt) return;
    const delay = expiresAt - Date.now() - REFRESH_BEFORE_MS;
    if (delay <= 0) { doRefresh(); return; }
    timerRef.current = setTimeout(doRefresh, delay);
  };

  useEffect(() => {
    scheduleRefresh();
    return () => { if (timerRef.current) clearTimeout(timerRef.current); };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
