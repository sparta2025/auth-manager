import { useNotificationSocket } from "../../hooks/useNotificationSocket";
import { useTheme } from "../../hooks/useTheme";
import { ThemeToggle } from "../ui/ThemeToggle";
import { useTokenRefresh } from "../../hooks/useTokenRefresh";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Shield, Users, Key, FileText, FolderOpen, Settings, LogOut, User, LayoutDashboard, Bell, ClipboardList, ChevronRight, Monitor, ShieldCheck, Lock } from "lucide-react";
import { useAuth } from "../../store/auth";
import { adminApi } from "../../api/admin";
import toast from "react-hot-toast";

export function AppLayout() {
  const { user, roles, logout, isAdmin, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  useTokenRefresh();
  useTheme(); // initialize theme on mount
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    if (!isAdmin) return;
    adminApi.getUnreadCount().then(d => setUnread(d.count)).catch(()=>{});
  }, [isAdmin]);

  useNotificationSocket(isAdmin && isAuthenticated && !!user, (n) => {
    setUnread(prev => prev + 1);
    if (n.title) toast(n.title, { icon: "🔔", duration: 5000 });
  });

  const handleLogout = async () => {
    await logout();
    toast.success("Сессия завершена");
    navigate("/login");
  };

  const adminNav = [
    { to: "/admin/users", icon: Users, label: "Пользователи" },
    { to: "/admin/roles", icon: Shield, label: "Роли" },
    { to: "/admin/permissions", icon: Key, label: "Разрешения" },
    { to: "/admin/notifications", icon: Bell, label: "Уведомления", badge: unread },
    { to: "/admin/audit-log", icon: ClipboardList, label: "Журнал аудита" },
    { to: "/admin/policy",    icon: Lock,         label: "Политика паролей" },
  ];
  const resourceNav = [
    { to: "/reports", icon: FileText, label: "Отчёты" },
    { to: "/documents", icon: FolderOpen, label: "Документы" },
    { to: "/settings", icon: Settings, label: "Настройки" },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="flex w-64 flex-col border-r border-gray-200 bg-white">
        <div className="flex h-16 items-center gap-2 border-b border-gray-100 px-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
            <Shield className="h-4 w-4 text-white"/>
          </div>
          <div>
            <p className="text-sm font-bold text-gray-900">Auth Manager</p>
            <p className="text-xs text-gray-400">v3.0</p>
          </div>
        </div>
        <div className="border-b border-gray-100 px-4 py-3 space-y-2">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 font-semibold text-sm">
              {user?.first_name?.[0]?.toUpperCase() ?? "?"}
            </div>
            <div className="min-w-0 leading-tight">
              <p className="truncate text-sm font-medium text-gray-900">{user?.first_name} {user?.last_name}</p>
              <p className="truncate text-xs text-gray-400">{roles?.[0]?.name ?? user?.email}</p>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <ThemeToggle />
            <button onClick={handleLogout} className="rounded-md p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600 transition-colors" title="Выйти">
              <LogOut className="h-4 w-4"/>
            </button>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-5">
          <Section title="Главная">
            <NavItem to="/dashboard" icon={LayoutDashboard} label="Обзор"/>
            <NavItem to="/profile" icon={User} label="Мой профиль"/>
            <NavItem to="/sessions" icon={Monitor} label="Мои сессии"/>
            <NavItem to="/2fa" icon={ShieldCheck} label="2FA защита"/>
          </Section>
          {isAdmin && (
            <Section title="Администрирование">
              {adminNav.map(({to,icon,label,badge})=>(
                <NavItem key={to} to={to} icon={icon} label={label} badge={badge}/>
              ))}
            </Section>
          )}
          <Section title="Ресурсы">
            {resourceNav.map(({to,icon,label})=>(
              <NavItem key={to} to={to} icon={icon} label={label}/>
            ))}
          </Section>
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto"><Outlet/></main>
    </div>
  );
}

function Section({ title, children }:{title:string;children:React.ReactNode}) {
  return (
    <div>
      <p className="mb-1 px-2 text-xs font-semibold uppercase tracking-wider text-gray-400">{title}</p>
      <ul className="space-y-0.5">{children}</ul>
    </div>
  );
}

function NavItem({ to, icon: Icon, label, badge }:{to:string;icon:React.ElementType;label:string;badge?:number}) {
  return (
    <li>
      <NavLink to={to} className={({isActive})=>`flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${isActive?"bg-blue-50 text-blue-700":"text-gray-600 hover:bg-gray-50 hover:text-gray-900"}`}>
        <Icon className="h-4 w-4 shrink-0"/>
        <span className="flex-1">{label}</span>
        {badge != null && badge > 0 && (
          <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1.5 text-xs font-bold text-white">{badge>99?"99+":badge}</span>
        )}
      </NavLink>
    </li>
  );
}

export function PageHeader({ title, subtitle, action, breadcrumb }:{title:string;subtitle?:string;action?:React.ReactNode;breadcrumb?:string[]}) {
  return (
    <div className="border-b border-gray-200 bg-white px-8 py-5">
      {breadcrumb&&<div className="mb-2 flex items-center gap-1 text-xs text-gray-400">{breadcrumb.map((c,i)=><span key={i} className="flex items-center gap-1">{i>0&&<ChevronRight className="h-3 w-3"/>}{c}</span>)}</div>}
      <div className="flex items-center justify-between">
        <div><h1 className="text-xl font-bold text-gray-900">{title}</h1>{subtitle&&<p className="mt-0.5 text-sm text-gray-500">{subtitle}</p>}</div>
        {action&&<div>{action}</div>}
      </div>
    </div>
  );
}
