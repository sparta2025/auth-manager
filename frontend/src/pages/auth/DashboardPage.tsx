import { useEffect, useState } from "react";
import { Users, Shield, Key, FileText, FolderOpen, Settings, Bell, ClipboardList } from "lucide-react";
import { Link } from "react-router-dom";
import { adminApi } from "../../api/admin";
import { reportsApi, documentsApi } from "../../api/resources";
import { useAuth } from "../../store/auth";
import { PageHeader } from "../../components/layout/AppLayout";
import { Spinner } from "../../components/ui";

export function DashboardPage() {
  const { user, isAdmin, hasPermission } = useAuth();
  const [stats, setStats] = useState<Record<string,number>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetches: Promise<void>[] = [];
    const s: Record<string,number> = {};

    if (isAdmin) {
      fetches.push(adminApi.getUsers().then(d=>{s.users=d.length}).catch(()=>{}));
      fetches.push(adminApi.getRoles().then(d=>{s.roles=d.length}).catch(()=>{}));
      fetches.push(adminApi.getPermissions().then(d=>{s.perms=d.length}).catch(()=>{}));
      fetches.push(adminApi.getUnreadCount().then(d=>{s.notifs=d.count}).catch(()=>{}));
    }
    if (hasPermission("reports:read")) fetches.push(reportsApi.getAll().then(d=>{s.reports=d.length}).catch(()=>{}));
    if (hasPermission("documents:read")) fetches.push(documentsApi.getAll().then(d=>{s.docs=d.length}).catch(()=>{}));

    Promise.all(fetches).then(()=>{setStats(s);setLoading(false);});
  }, [isAdmin, hasPermission]);

  const adminCards = [
    {to:"/admin/users",icon:Users,label:"Пользователи",key:"users",color:"blue"},
    {to:"/admin/roles",icon:Shield,label:"Роли",key:"roles",color:"violet"},
    {to:"/admin/permissions",icon:Key,label:"Разрешения",key:"perms",color:"indigo"},
    {to:"/admin/notifications",icon:Bell,label:"Уведомления",key:"notifs",color:"orange"},
  ];
  const resourceCards = [
    {to:"/reports",icon:FileText,label:"Отчёты",key:"reports",color:"emerald",perm:"reports:read"},
    {to:"/documents",icon:FolderOpen,label:"Документы",key:"docs",color:"amber",perm:"documents:read"},
    {to:"/settings",icon:Settings,label:"Настройки",key:null,color:"gray",perm:"settings:read"},
  ];
  const colorMap: Record<string,string> = {
    blue:"bg-blue-50 text-blue-600",violet:"bg-violet-50 text-violet-600",
    indigo:"bg-indigo-50 text-indigo-600",orange:"bg-orange-50 text-orange-600",
    emerald:"bg-emerald-50 text-emerald-600",amber:"bg-amber-50 text-amber-600",
    gray:"bg-gray-100 text-gray-600",
  };

  return (
    <>
      <PageHeader title={`Добро пожаловать, ${user?.first_name}!`} subtitle="Панель управления Auth Manager" breadcrumb={["Главная","Обзор"]}/>
      <div className="p-8 space-y-8">
        {isAdmin && (
          <div>
            <h2 className="mb-3 text-sm font-semibold text-gray-500 uppercase tracking-wide">Администрирование</h2>
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              {adminCards.map(({to,icon:Icon,label,key,color})=>(
                <Link key={to} to={to} className="card p-5 hover:shadow-md transition-shadow">
                  <div className={`mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl ${colorMap[color]}`}><Icon className="h-5 w-5"/></div>
                  <p className="text-sm text-gray-500">{label}</p>
                  <p className="mt-0.5 text-2xl font-bold text-gray-900">
                    {loading?<Spinner className="h-5 w-5 text-gray-300"/>:(stats[key]??0)}
                  </p>
                </Link>
              ))}
            </div>
          </div>
        )}
        <div>
          <h2 className="mb-3 text-sm font-semibold text-gray-500 uppercase tracking-wide">Ресурсы</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {resourceCards.filter(c=>hasPermission(c.perm)).map(({to,icon:Icon,label,key,color})=>(
              <Link key={to} to={to} className="card p-5 hover:shadow-md transition-shadow">
                <div className={`mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl ${colorMap[color]}`}><Icon className="h-5 w-5"/></div>
                <p className="text-sm text-gray-500">{label}</p>
                {key && <p className="mt-0.5 text-2xl font-bold text-gray-900">{loading?<Spinner className="h-5 w-5 text-gray-300"/>:(stats[key]??0)}</p>}
              </Link>
            ))}
          </div>
        </div>
        {isAdmin && (
          <div>
            <h2 className="mb-3 text-sm font-semibold text-gray-500 uppercase tracking-wide">Быстрый доступ</h2>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              {[
                {to:"/admin/notifications",icon:Bell,label:"Непрочитанные уведомления",desc:`${stats.notifs??0} ожидают вашего внимания`},
                {to:"/admin/audit-log",icon:ClipboardList,label:"Журнал аудита",desc:"История всех действий в системе"},
              ].map(({to,icon:Icon,label,desc})=>(
                <Link key={to} to={to} className="card flex items-start gap-4 p-4 hover:shadow-md transition-shadow">
                  <div className="mt-0.5 rounded-lg bg-gray-100 p-2 text-gray-600"><Icon className="h-4 w-4"/></div>
                  <div><p className="text-sm font-medium text-gray-900">{label}</p><p className="mt-0.5 text-xs text-gray-500">{desc}</p></div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
