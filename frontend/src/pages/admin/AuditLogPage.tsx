import { useCallback, useEffect, useState } from "react";
import { ClipboardList, Search, Download } from "lucide-react";
import { adminApi } from "../../api/admin";
import { getErrorMessage } from "../../api/client";
import type { AuditEntry } from "../../types";
import { EmptyState, PageLoader, Table } from "../../components/ui";
import { PageHeader } from "../../components/layout/AppLayout";
import toast from "react-hot-toast";

const ACTION_COLOR: Record<string,string> = {
  "user.login":"bg-green-100 text-green-700",
  "user.logout":"bg-gray-100 text-gray-600",
  "user.registered":"bg-blue-100 text-blue-700",
  "user.profile_updated":"bg-amber-100 text-amber-700",
  "user.self_deactivated":"bg-red-100 text-red-700",
  "user.password_changed":"bg-violet-100 text-violet-700",
  "user.password_reset_requested":"bg-orange-100 text-orange-700",
  "admin.user_deleted":"bg-red-200 text-red-800",
};

export function AuditLogPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [actionFilter, setActionFilter] = useState("");

  const load = useCallback(async()=>{
    setLoading(true);
    try { setEntries(await adminApi.getAuditLog({action:actionFilter||undefined,limit:200})); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setLoading(false); }
  },[actionFilter]);

  useEffect(()=>{load();},[load]);

  const filtered = entries.filter(e=>{
    const q=search.toLowerCase();
    return (e.user_email?.toLowerCase().includes(q)||e.action.toLowerCase().includes(q)||e.detail?.toLowerCase().includes(q));
  });

  if (loading) return <PageLoader/>;

  return (
    <>
      <PageHeader title="Журнал аудита" subtitle={`${entries.length} событий`} breadcrumb={["Администрирование","Журнал аудита"]}
        action={<a href="/admin/audit-log/export/csv" download className="btn-secondary text-sm"><Download className="h-4 w-4"/>Экспорт CSV</a>}/>
      <div className="p-8 space-y-4">
        <div className="flex gap-3 flex-wrap">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400"/>
            <input className="input pl-9" placeholder="Поиск по email, действию, деталям…" value={search} onChange={e=>setSearch(e.target.value)}/>
          </div>
          <select className="input w-auto" value={actionFilter} onChange={e=>setActionFilter(e.target.value)}>
            <option value="">Все действия</option>
            {["user.login","user.logout","user.registered","user.profile_updated","user.self_deactivated","user.password_changed","admin.user_deleted","admin.roles_assigned"].map(a=><option key={a} value={a}>{a}</option>)}
          </select>
        </div>
        {filtered.length===0 ? <EmptyState icon={<ClipboardList className="h-12 w-12"/>} title="Нет записей"/> : (
          <Table headers={["Время","Пользователь","Действие","Тип/ID","IP","Детали"]}>
            {filtered.map(e=>(
              <tr key={e.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">{new Date(e.created_at).toLocaleString("ru-RU")}</td>
                <td className="px-4 py-3 text-sm text-gray-700">{e.user_email??<span className="text-gray-300">система</span>}</td>
                <td className="px-4 py-3"><span className={`badge text-xs font-mono ${ACTION_COLOR[e.action]??"bg-gray-100 text-gray-700"}`}>{e.action}</span></td>
                <td className="px-4 py-3 text-xs text-gray-400">{e.entity_type&&<span className="font-medium text-gray-600">{e.entity_type}</span>}{e.entity_id&&<span className="ml-1 font-mono">{e.entity_id.slice(0,8)}…</span>}</td>
                <td className="px-4 py-3 text-xs text-gray-400 font-mono">{e.ip_address??"-"}</td>
                <td className="px-4 py-3 text-xs text-gray-500 max-w-xs truncate">{e.detail??"-"}</td>
              </tr>
            ))}
          </Table>
        )}
      </div>
    </>
  );
}
