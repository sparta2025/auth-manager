import { apiClient } from "../../api/client";
import { useState } from "react";
import { User, Mail, Calendar, Shield, Key, Edit2, Check, X, Lock, Monitor, Camera } from "lucide-react";
import { useAuth } from "../../store/auth";
import { authApi } from "../../api/auth";
import { getErrorMessage } from "../../api/client";
import { Alert, ConfirmModal, DangerZone, Spinner, StatusBadge } from "../../components/ui";
import { PageHeader } from "../../components/layout/AppLayout";
import toast from "react-hot-toast";
import { useNavigate } from "react-router-dom";

export function ProfilePage() {
  const { user, roles, permissions, refresh, logout } = useAuth();
  const navigate = useNavigate();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ first_name:user?.first_name??"", last_name:user?.last_name??"", middle_name:user?.middle_name??"", recovery_email:user?.recovery_email??"" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [showDeactivate, setShowDeactivate] = useState(false);
  const [deactivating, setDeactivating] = useState(false);
  // Password change
  const [pwForm, setPwForm] = useState({ current_password:"", new_password:"", new_password_repeat:"" });
  const [pwError, setPwError] = useState("");
  const [pwSaving, setPwSaving] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const handleSave = async () => {
    setSaving(true); setError("");
    try {
      await authApi.updateProfile({ first_name:form.first_name||undefined, last_name:form.last_name||undefined, middle_name:form.middle_name||undefined, recovery_email:form.recovery_email||undefined });
      await refresh(); setEditing(false); toast.success("Профиль обновлён");
    } catch(err) { setError(getErrorMessage(err)); }
    finally { setSaving(false); }
  };

  const handleDeactivate = async () => {
    setDeactivating(true);
    try { await authApi.deleteAccount(); await logout(); navigate("/login"); toast.success("Аккаунт деактивирован"); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setDeactivating(false); setShowDeactivate(false); }
  };

  const handlePwChange = async (e: React.FormEvent) => {
    e.preventDefault(); setPwError(""); setPwSaving(true);
    try { await authApi.changePassword(pwForm); toast.success("Пароль изменён"); setShowPw(false); setPwForm({current_password:"",new_password:"",new_password_repeat:""}); }
    catch(err) { setPwError(getErrorMessage(err)); }
    finally { setPwSaving(false); }
  };

  if (!user) return null;

  const handleAvatarUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    try {
      await apiClient.post("/auth/avatar", fd, { headers: { "Content-Type": "multipart/form-data" } });
      await refresh();
      toast.success("Аватар обновлён");
    } catch (err) { toast.error(getErrorMessage(err)); }
  };

  return (
    <>
      <PageHeader title="Мой профиль" subtitle="Управление личными данными" breadcrumb={["Главная","Профиль"]}/>
      <div className="p-8 max-w-2xl space-y-6">
        {/* Main card */}
        <div className="card p-6 space-y-5">
          <div className="flex items-center gap-4">
            <div className="relative">
              {user.avatar_url
                ? <img src={user.avatar_url} alt="avatar" className="h-16 w-16 rounded-full object-cover"/>
                : <div className="flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-2xl font-bold">{user.first_name[0]?.toUpperCase()}</div>
              }
              <label className="absolute -bottom-1 -right-1 flex h-6 w-6 cursor-pointer items-center justify-center rounded-full bg-blue-600 text-white shadow hover:bg-blue-700">
                <Camera className="h-3 w-3"/>
                <input type="file" className="sr-only" accept="image/*" onChange={handleAvatarUpload}/>
              </label>
            </div>
            <div><h2 className="text-lg font-semibold text-gray-900">{user.first_name} {user.last_name}</h2><StatusBadge active={user.is_active}/></div>
          </div>
          {error && <Alert type="error" message={error}/>}
          {editing ? (
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div><label className="label">Имя</label><input className="input" value={form.first_name} onChange={e=>setForm(f=>({...f,first_name:e.target.value}))}/></div>
                <div><label className="label">Фамилия</label><input className="input" value={form.last_name} onChange={e=>setForm(f=>({...f,last_name:e.target.value}))}/></div>
              </div>
              <div><label className="label">Отчество</label><input className="input" value={form.middle_name} onChange={e=>setForm(f=>({...f,middle_name:e.target.value}))}/></div>
              <div>
                <label className="label">Резервный email (для сброса пароля)</label>
                <input className="input" type="email" value={form.recovery_email} onChange={e=>setForm(f=>({...f,recovery_email:e.target.value}))} placeholder="Необязательно"/>
              </div>
              <div className="flex gap-2 pt-1">
                <button className="btn-primary" onClick={handleSave} disabled={saving}>{saving?<Spinner/>:<Check className="h-4 w-4"/>}Сохранить</button>
                <button className="btn-secondary" onClick={()=>setEditing(false)}><X className="h-4 w-4"/>Отмена</button>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <InfoRow icon={<User className="h-4 w-4"/>} label="Полное имя" value={[user.first_name,user.middle_name,user.last_name].filter(Boolean).join(" ")}/>
              <InfoRow icon={<Mail className="h-4 w-4"/>} label="Email (вход)" value={user.email}/>
              <InfoRow icon={<Mail className="h-4 w-4"/>} label="Резервный email" value={user.recovery_email ?? "не указан"}/>
              <InfoRow icon={<Calendar className="h-4 w-4"/>} label="Зарегистрирован" value={new Date(user.created_at).toLocaleString("ru-RU")}/>
              {user.last_login_at && <InfoRow icon={<Monitor className="h-4 w-4"/>} label="Последний вход" value={new Date(user.last_login_at).toLocaleString("ru-RU")}/>}
              <button className="btn-secondary" onClick={()=>setEditing(true)}><Edit2 className="h-4 w-4"/>Редактировать</button>
            </div>
          )}
        </div>

        {/* Roles (read-only for non-admins) */}
        <div className="card p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700"><Shield className="h-4 w-4 text-blue-500"/>Мои роли</h3>
          {roles.length === 0 ? <p className="text-sm text-gray-400">Роли не назначены</p> : (
            <div className="flex flex-wrap gap-2">{roles.map(r=><span key={r.id} className="badge bg-blue-100 text-blue-700 px-3 py-1">{r.name}</span>)}</div>
          )}
        </div>

        {/* Permissions (read-only) */}
        <div className="card p-5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-gray-700"><Key className="h-4 w-4 text-violet-500"/>Мои разрешения</h3>
          {permissions.length === 0 ? <p className="text-sm text-gray-400">Нет разрешений</p> : (
            <div className="flex flex-wrap gap-1.5">{permissions.map(p=><span key={p} className="badge bg-violet-50 text-violet-700 font-mono text-xs px-2 py-0.5">{p}</span>)}</div>
          )}
        </div>

        {/* Change password */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-700"><Lock className="h-4 w-4 text-gray-400"/>Смена пароля</h3>
            <button className="btn-secondary text-xs" onClick={()=>setShowPw(v=>!v)}>{showPw?"Свернуть":"Изменить пароль"}</button>
          </div>
          {showPw && (
            <form onSubmit={handlePwChange} className="space-y-3">
              {pwError && <Alert type="error" message={pwError}/>}
              <div><label className="label">Текущий пароль</label><input className="input" type="password" value={pwForm.current_password} onChange={e=>setPwForm(f=>({...f,current_password:e.target.value}))} required/></div>
              <div><label className="label">Новый пароль</label><input className="input" type="password" value={pwForm.new_password} onChange={e=>setPwForm(f=>({...f,new_password:e.target.value}))} required/></div>
              <div><label className="label">Повторите</label><input className="input" type="password" value={pwForm.new_password_repeat} onChange={e=>setPwForm(f=>({...f,new_password_repeat:e.target.value}))} required/></div>
              <button type="submit" className="btn-primary" disabled={pwSaving}>{pwSaving&&<Spinner/>}Сохранить пароль</button>
            </form>
          )}
        </div>

        {/* Danger zone */}
        <DangerZone>
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-semibold text-red-800">Деактивировать аккаунт</p>
              <p className="text-xs text-red-600 mt-0.5">Все сессии будут завершены. Администратор получит уведомление. Восстановление — только через администратора.</p>
            </div>
            <button className="btn-danger shrink-0 ml-4" onClick={()=>setShowDeactivate(true)}>Деактивировать</button>
          </div>
        </DangerZone>
      </div>

      <ConfirmModal open={showDeactivate} onClose={()=>setShowDeactivate(false)} onConfirm={handleDeactivate}
        title="Деактивировать аккаунт?" danger loading={deactivating}
        message="Вы уверены? Аккаунт будет деактивирован. Все активные сессии завершатся. Администратор получит уведомление. Для восстановления обратитесь к администратору."/>
    </>
  );
}
function InfoRow({icon,label,value}:{icon:React.ReactNode;label:string;value:string}) {
  return <div className="flex items-start gap-3"><div className="mt-0.5 text-gray-400">{icon}</div><div><p className="text-xs text-gray-500">{label}</p><p className="text-sm font-medium text-gray-900">{value}</p></div></div>;
}
