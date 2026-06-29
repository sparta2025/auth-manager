import { useCallback, useEffect, useState } from "react";
import { Bell, CheckCheck, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { adminApi } from "../../api/admin";
import { getErrorMessage } from "../../api/client";
import type { Notification } from "../../types";
import { EmptyState, PageLoader, Spinner } from "../../components/ui";
import { PageHeader } from "../../components/layout/AppLayout";
import toast from "react-hot-toast";

const EVENT_STYLE: Record<string,string> = {
  registered:"bg-green-100 text-green-700",
  profile_updated:"bg-blue-100 text-blue-700",
  deactivated:"bg-red-100 text-red-700",
};
const EVENT_LABEL: Record<string,string> = {
  registered:"Регистрация",
  profile_updated:"Изменение профиля",
  deactivated:"Деактивация",
};

export function NotificationsPage() {
  const [notifs, setNotifs] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [markingAll, setMarkingAll] = useState(false);
  const [unreadOnly, setUnreadOnly] = useState(false);

  const load = useCallback(async()=>{
    setLoading(true);
    try { setNotifs(await adminApi.getNotifications(unreadOnly)); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setLoading(false); }
  },[unreadOnly]);

  useEffect(()=>{load();},[load]);

  const markRead = async(id: string)=>{
    await adminApi.markRead(id).catch(()=>{});
    setNotifs(n=>n.map(x=>x.id===id?{...x,is_read:true}:x));
  };

  const markAll = async()=>{
    setMarkingAll(true);
    try { await adminApi.markAllRead(); setNotifs(n=>n.map(x=>({...x,is_read:true}))); toast.success("Все прочитаны"); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setMarkingAll(false); }
  };

  const unreadCount = notifs.filter(n=>!n.is_read).length;
  if (loading) return <PageLoader/>;

  return (
    <>
      <PageHeader title="Уведомления" subtitle={`${unreadCount} непрочитанных`} breadcrumb={["Администрирование","Уведомления"]}
        action={
          <div className="flex items-center gap-2">
            <button className={`btn-secondary text-sm ${unreadOnly?"ring-2 ring-blue-400":""}`} onClick={()=>setUnreadOnly(v=>!v)}>
              {unreadOnly?"Все":"Непрочитанные"}
            </button>
            {unreadCount>0&&<button className="btn-secondary" onClick={markAll} disabled={markingAll}>{markingAll?<Spinner/>:<CheckCheck className="h-4 w-4"/>}Прочитать все</button>}
          </div>
        }/>
      <div className="p-8">
        {notifs.length===0 ? (
          <EmptyState icon={<Bell className="h-12 w-12"/>} title={unreadOnly?"Нет непрочитанных":"Нет уведомлений"}/>
        ) : (
          <div className="space-y-2">
            {notifs.map(n=>(
              <div key={n.id} className={`card p-4 flex items-start gap-4 transition-all ${n.is_read?"opacity-60":""}`}>
                <div className={`mt-0.5 h-2.5 w-2.5 rounded-full shrink-0 ${n.is_read?"bg-gray-200":"bg-blue-500"}`}/>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`badge text-xs ${EVENT_STYLE[n.event]??"bg-gray-100 text-gray-600"}`}>{EVENT_LABEL[n.event]??n.event}</span>
                    <span className="text-xs text-gray-400">{new Date(n.created_at).toLocaleString("ru-RU")}</span>
                  </div>
                  <p className="text-sm font-medium text-gray-900">{n.title}</p>
                  {n.body&&<p className="text-xs text-gray-500 mt-0.5">{n.body}</p>}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {n.link&&(
                    <Link to={n.link} className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-blue-600 hover:bg-blue-50">
                      <ExternalLink className="h-3.5 w-3.5"/>Открыть
                    </Link>
                  )}
                  {!n.is_read&&(
                    <button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-500 hover:bg-gray-100" onClick={()=>markRead(n.id)}>
                      <CheckCheck className="h-3.5 w-3.5"/>Прочитано
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
