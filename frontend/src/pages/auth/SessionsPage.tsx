import { useEffect, useState } from "react";
import { Monitor, Smartphone, Trash2, Globe } from "lucide-react";
import { authApi } from "../../api/auth";
import { getErrorMessage } from "../../api/client";
import type { SessionInfo } from "../../types";
import { ConfirmModal, EmptyState, PageLoader, Table } from "../../components/ui";
import { PageHeader } from "../../components/layout/AppLayout";
import toast from "react-hot-toast";

function DeviceIcon({ ua }: { ua: string | null }) {
  if (!ua) return <Globe className="h-4 w-4 text-gray-400" />;
  const lower = ua.toLowerCase();
  if (lower.includes("mobile") || lower.includes("android") || lower.includes("iphone"))
    return <Smartphone className="h-4 w-4 text-blue-500" />;
  return <Monitor className="h-4 w-4 text-gray-500" />;
}

function parseUA(ua: string | null): string {
  if (!ua) return "Неизвестное устройство";
  if (ua.includes("Chrome")) return "Chrome";
  if (ua.includes("Firefox")) return "Firefox";
  if (ua.includes("Safari")) return "Safari";
  if (ua.includes("Edge")) return "Edge";
  return ua.slice(0, 40) + "…";
}

export function SessionsPage() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [revokeTarget, setRevokeTarget] = useState<SessionInfo | null>(null);
  const [revoking, setRevoking] = useState(false);

  const load = async () => {
    setLoading(true);
    try { setSessions(await authApi.mySessions()); }
    catch (err) { toast.error(getErrorMessage(err)); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleRevoke = async () => {
    if (!revokeTarget) return;
    setRevoking(true);
    try {
      await authApi.revokeSession(revokeTarget.id);
      toast.success("Сессия завершена");
      setRevokeTarget(null);
      await load();
    } catch (err) { toast.error(getErrorMessage(err)); }
    finally { setRevoking(false); }
  };


  if (loading) return <PageLoader />;

  return (
    <>
      <PageHeader
        title="Мои сессии"
        subtitle={`Активных: ${sessions.length}`}
        breadcrumb={["Главная", "Мои сессии"]}
      />
      <div className="p-8 max-w-3xl">
        <div className="mb-4 rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-sm text-blue-700">
          Здесь показаны все ваши активные сессии. Вы можете завершить любую из них кроме текущей.
          При обнаружении незнакомой сессии — немедленно завершите её и смените пароль.
        </div>

        {sessions.length === 0 ? (
          <EmptyState icon={<Monitor className="h-12 w-12" />} title="Нет активных сессий" />
        ) : (
          <Table headers={["Устройство", "IP-адрес", "Создана", "Истекает", ""]}>
            {sessions.map((s, idx) => (
              <tr key={s.id} className={`hover:bg-gray-50 ${idx === 0 ? "bg-blue-50/40" : ""}`}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <DeviceIcon ua={s.user_agent} />
                    <div>
                      <p className="text-sm font-medium text-gray-900">{parseUA(s.user_agent)}</p>
                      {idx === 0 && (
                        <span className="badge bg-blue-100 text-blue-700 text-xs">Текущая</span>
                      )}
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm font-mono text-gray-500">
                  {s.ip_address ?? "—"}
                </td>
                <td className="px-4 py-3 text-xs text-gray-500">
                  {new Date(s.created_at).toLocaleString("ru-RU")}
                </td>
                <td className="px-4 py-3 text-xs text-gray-500">
                  {new Date(s.expires_at).toLocaleString("ru-RU")}
                </td>
                <td className="px-4 py-3">
                  {idx !== 0 && (
                    <button
                      className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                      onClick={() => setRevokeTarget(s)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                      Завершить
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </Table>
        )}
      </div>

      <ConfirmModal
        open={!!revokeTarget}
        onClose={() => setRevokeTarget(null)}
        onConfirm={handleRevoke}
        title="Завершить сессию?"
        message="Выбранная сессия будет немедленно завершена. Пользователь на этом устройстве будет разлогинен."
        danger
        loading={revoking}
      />
    </>
  );
}
