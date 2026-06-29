/**
 * WebSocket hook для real-time уведомлений администратора.
 * Подключается к /ws/notifications?token=<access_token>.
 * При получении события вызывает onNotification callback.
 */
import { useEffect, useRef } from "react";

type NotificationPayload = {
  type: "notification" | "ping";
  event?: string;
  title?: string;
  body?: string;
  link?: string;
};

export function useNotificationSocket(
  enabled: boolean,
  onNotification: (n: NotificationPayload) => void
) {
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryCount = useRef(0);

  useEffect(() => {
    if (!enabled) return;

    const connect = () => {
      const token = localStorage.getItem("access_token");
      if (!token) return;

      // Determine WS URL — same host, replace http→ws
      const base = window.location.origin.replace(/^http/, "ws");
      const url  = `${base}/ws/notifications?token=${token}`;

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => { retryCount.current = 0; };

      ws.onmessage = (evt) => {
        try {
          const data: NotificationPayload = JSON.parse(evt.data);
          if (data.type === "notification") onNotification(data);
        } catch { /* ignore malformed */ }
      };

      ws.onclose = () => {
        // Exponential backoff: 2s, 4s, 8s … max 30s
        const delay = Math.min(30000, 2000 * 2 ** retryCount.current);
        retryCount.current++;
        retryRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => ws.close();
    };

    connect();

    return () => {
      wsRef.current?.close();
      if (retryRef.current) clearTimeout(retryRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled]);
}
