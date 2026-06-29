import { useCallback, useEffect, useState } from "react";
import { Plus, Users, Search, Shield, Eye, UserX, UserCheck, Trash2, Key, LogOut, Download } from "lucide-react";
import { adminApi } from "../../api/admin";
import { getErrorMessage } from "../../api/client";
import type { Role, User } from "../../types";
import { ConfirmModal, DangerZone, EmptyState, Modal, PageLoader, Spinner, StatusBadge, Table } from "../../components/ui";
import { PageHeader } from "../../components/layout/AppLayout";
import toast from "react-hot-toast";

export function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterActive, setFilterActive] = useState<"all"|"active"|"inactive">("all");

  // Detail / edit modal
  const [detailUser, setDetailUser] = useState<User|null>(null);
  const [editForm, setEditForm] = useState({ first_name:"", last_name:"", middle_name:"", recovery_email:"" });
  const [editSaving, setEditSaving] = useState(false);

  // Role assignment
  const [roleUser, setRoleUser] = useState<User|null>(null);
  const [userRoleIds, setUserRoleIds] = useState<string[]>([]);
  const [roleSaving, setRoleSaving] = useState(false);

  // Password modal
  const [pwUser, setPwUser] = useState<User|null>(null);
  const [newPw, setNewPw] = useState("");
  const [pwSaving, setPwSaving] = useState(false);

  // Create user modal
  const [createOpen, setCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({ first_name:"", last_name:"", middle_name:"", email:"", password:"" });
  const [createRoleIds, setCreateRoleIds] = useState<string[]>([]);
  const [createSaving, setCreateSaving] = useState(false);

  // Confirm modals
  const [confirmUser, setConfirmUser] = useState<User|null>(null);
  const [confirmAction, setConfirmAction] = useState<"activate"|"deactivate"|"delete"|"logout">("deactivate");
  const [actionLoading, setActionLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [u,r] = await Promise.all([adminApi.getUsers(), adminApi.getRoles()]);
      setUsers(u); setRoles(r);
    } catch(err) { toast.error(getErrorMessage(err)); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = users.filter(u => {
    const q = search.toLowerCase();
    const match = u.email.toLowerCase().includes(q) || `${u.first_name} ${u.last_name}`.toLowerCase().includes(q);
    if (filterActive === "active" && !u.is_active) return false;
    if (filterActive === "inactive" && u.is_active) return false;
    return match;
  });

  const openDetail = (u: User) => {
    setDetailUser(u);
    setEditForm({ first_name:u.first_name, last_name:u.last_name, middle_name:u.middle_name??"", recovery_email:u.recovery_email??"" });
  };

  const handleEditSave = async () => {
    if (!detailUser) return;
    setEditSaving(true);
    try {
      await adminApi.updateUser(detailUser.id, { first_name:editForm.first_name||undefined, last_name:editForm.last_name||undefined, middle_name:editForm.middle_name||undefined, recovery_email:editForm.recovery_email||undefined });
      toast.success("Профиль обновлён"); await load();
      const updated = await adminApi.getUser(detailUser.id); setDetailUser(updated);
    } catch(err) { toast.error(getErrorMessage(err)); }
    finally { setEditSaving(false); }
  };

  const openRoles = async (u: User) => {
    setRoleUser(u); setRoleSaving(true);
    try { const {roles:r} = await adminApi.getUserRoles(u.id); setUserRoleIds(r.map(x=>x.id)); }
    catch { setUserRoleIds([]); }
    finally { setRoleSaving(false); }
  };

  const handleSaveRoles = async () => {
    if (!roleUser) return; setRoleSaving(true);
    try { await adminApi.assignRoles(roleUser.id, userRoleIds); toast.success("Роли назначены"); setRoleUser(null); await load(); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setRoleSaving(false); }
  };

  const handleSetPassword = async () => {
    if (!pwUser||!newPw) return; setPwSaving(true);
    try { await adminApi.setPassword(pwUser.id, newPw); toast.success("Пароль установлен"); setPwUser(null); setNewPw(""); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setPwSaving(false); }
  };

  const handleConfirm = async () => {
    if (!confirmUser) return; setActionLoading(true);
    try {
      if (confirmAction==="activate") { await adminApi.activateUser(confirmUser.id); toast.success("Пользователь активирован"); }
      else if (confirmAction==="deactivate") { await adminApi.deactivateUser(confirmUser.id); toast.success("Пользователь деактивирован"); }
      else if (confirmAction==="delete") { await adminApi.deleteUser(confirmUser.id); toast.success("Пользователь удалён"); }
      else if (confirmAction==="logout") { await adminApi.logoutAll(confirmUser.id); toast.success("Все сессии завершены"); }
      await load(); setConfirmUser(null);
    } catch(err) { toast.error(getErrorMessage(err)); }
    finally { setActionLoading(false); }
  };

  const handleCreate = async () => {
    setCreateSaving(true);
    try {
      await adminApi.createUser({ ...createForm, role_ids: createRoleIds });
      toast.success("Пользователь создан"); setCreateOpen(false);
      setCreateForm({ first_name:"", last_name:"", middle_name:"", email:"", password:"" });
      setCreateRoleIds([]); await load();
    } catch(err) { toast.error(getErrorMessage(err)); }
    finally { setCreateSaving(false); }
  };

  if (loading) return <PageLoader/>;

  return (
    <>
      <PageHeader title="Пользователи" subtitle={`Всего: ${users.length}`} breadcrumb={["Администрирование","Пользователи"]}
        action={<button className="btn-primary" onClick={()=>setCreateOpen(true)}><Plus className="h-4 w-4"/>Создать</button>}/>
      <div className="p-8 space-y-4">
        {/* Export */}
        <div className="flex justify-end mb-2">
          <a href="/admin/users/export/csv" download className="btn-secondary text-xs">
            <Download className="h-3.5 w-3.5"/>Экспорт CSV
          </a>
        </div>
        {/* Filters */}
        <div className="flex gap-3 flex-wrap">
          <div className="relative flex-1 min-w-48">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400"/>
            <input className="input pl-9" placeholder="Поиск по имени или email..." value={search} onChange={e=>setSearch(e.target.value)}/>
          </div>
          <div className="flex rounded-lg border border-gray-200 bg-white overflow-hidden">
            {(["all","active","inactive"] as const).map(v=>(
              <button key={v} onClick={()=>setFilterActive(v)} className={`px-3 py-2 text-sm font-medium transition-colors ${filterActive===v?"bg-blue-600 text-white":"text-gray-600 hover:bg-gray-50"}`}>
                {v==="all"?"Все":v==="active"?"Активные":"Деактивированные"}
              </button>
            ))}
          </div>
        </div>

        {filtered.length===0 ? (
          <EmptyState icon={<Users className="h-12 w-12"/>} title="Пользователи не найдены"/>
        ) : (
          <Table headers={["Пользователь","Email","Статус","Последний вход","Действия"]}>
            {filtered.map(u=>(
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-700 text-sm font-semibold">{u.first_name[0]?.toUpperCase()}</div>
                    <div><p className="font-medium text-gray-900">{u.first_name} {u.last_name}</p><p className="text-xs text-gray-400">{u.id.slice(0,8)}…</p></div>
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-700 text-sm">{u.email}</td>
                <td className="px-4 py-3"><StatusBadge active={u.is_active}/></td>
                <td className="px-4 py-3 text-xs text-gray-400">{u.last_login_at?new Date(u.last_login_at).toLocaleString("ru-RU"):"—"}</td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1 flex-wrap">
                    <button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100" onClick={()=>openDetail(u)}><Eye className="h-3.5 w-3.5"/>Профиль</button>
                    <button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-blue-600 hover:bg-blue-50" onClick={()=>openRoles(u)}><Shield className="h-3.5 w-3.5"/>Роли</button>
                    <button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-violet-600 hover:bg-violet-50" onClick={()=>{setPwUser(u);setNewPw("");}}><Key className="h-3.5 w-3.5"/>Пароль</button>
                    <button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-amber-600 hover:bg-amber-50" onClick={()=>{setConfirmUser(u);setConfirmAction("logout");}}><LogOut className="h-3.5 w-3.5"/>Сессии</button>
                    {u.is_active
                      ? <button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50" onClick={()=>{setConfirmUser(u);setConfirmAction("deactivate");}}><UserX className="h-3.5 w-3.5"/>Деактив.</button>
                      : <button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-green-600 hover:bg-green-50" onClick={()=>{setConfirmUser(u);setConfirmAction("activate");}}><UserCheck className="h-3.5 w-3.5"/>Активир.</button>
                    }
                    <button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-red-700 hover:bg-red-50 font-semibold" onClick={()=>{setConfirmUser(u);setConfirmAction("delete");}}><Trash2 className="h-3.5 w-3.5"/>Удалить</button>
                  </div>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </div>

      {/* Create user modal */}
      <Modal open={createOpen} onClose={()=>setCreateOpen(false)} title="Создать пользователя">
        <div className="space-y-3 mb-6">
          <div className="grid grid-cols-2 gap-3">
            <div><label className="label">Имя *</label><input className="input" value={createForm.first_name} onChange={e=>setCreateForm(f=>({...f,first_name:e.target.value}))} autoFocus/></div>
            <div><label className="label">Фамилия *</label><input className="input" value={createForm.last_name} onChange={e=>setCreateForm(f=>({...f,last_name:e.target.value}))}/></div>
          </div>
          <div><label className="label">Отчество</label><input className="input" value={createForm.middle_name} onChange={e=>setCreateForm(f=>({...f,middle_name:e.target.value}))}/></div>
          <div><label className="label">Email *</label><input className="input" type="email" value={createForm.email} onChange={e=>setCreateForm(f=>({...f,email:e.target.value}))}/></div>
          <div><label className="label">Пароль *</label><input className="input" type="password" value={createForm.password} onChange={e=>setCreateForm(f=>({...f,password:e.target.value}))} placeholder="Мин. 8 символов"/></div>
          <div><label className="label">Роли</label>
            <div className="space-y-2 mt-1 max-h-40 overflow-y-auto">
              {roles.map(role=>(
                <label key={role.id} className="flex items-center gap-2 rounded border border-gray-200 px-3 py-2 cursor-pointer hover:bg-gray-50">
                  <input type="checkbox" className="h-4 w-4 rounded border-gray-300 text-blue-600"
                    checked={createRoleIds.includes(role.id)}
                    onChange={e=>setCreateRoleIds(p=>e.target.checked?[...p,role.id]:p.filter(id=>id!==role.id))}/>
                  <span className="text-sm text-gray-700">{role.name}</span>
                </label>
              ))}
            </div>
          </div>
        </div>
        <div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={()=>setCreateOpen(false)}>Отмена</button>
          <button className="btn-primary" onClick={handleCreate} disabled={createSaving||!createForm.first_name||!createForm.last_name||!createForm.email||!createForm.password}>{createSaving&&<Spinner/>}Создать</button>
        </div>
      </Modal>

      {/* Detail/Edit modal */}
      <Modal open={!!detailUser} onClose={()=>setDetailUser(null)} title={`Профиль: ${detailUser?.email}`} size="lg">
        {detailUser && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <div><label className="label">Имя</label><input className="input" value={editForm.first_name} onChange={e=>setEditForm(f=>({...f,first_name:e.target.value}))}/></div>
              <div><label className="label">Фамилия</label><input className="input" value={editForm.last_name} onChange={e=>setEditForm(f=>({...f,last_name:e.target.value}))}/></div>
            </div>
            <div><label className="label">Отчество</label><input className="input" value={editForm.middle_name} onChange={e=>setEditForm(f=>({...f,middle_name:e.target.value}))}/></div>
            <div><label className="label">Резервный email</label><input className="input" type="email" value={editForm.recovery_email} onChange={e=>setEditForm(f=>({...f,recovery_email:e.target.value}))}/></div>
            <div className="rounded-lg bg-gray-50 p-3 text-xs text-gray-500 space-y-1">
              <p>Email (вход): <strong>{detailUser.email}</strong></p>
              <p>Статус: <strong>{detailUser.is_active?"Активен":"Деактивирован"}</strong></p>
              <p>Создан: <strong>{new Date(detailUser.created_at).toLocaleString("ru-RU")}</strong></p>
              {detailUser.last_login_at&&<p>Последний вход: <strong>{new Date(detailUser.last_login_at).toLocaleString("ru-RU")}</strong></p>}
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button className="btn-secondary" onClick={()=>setDetailUser(null)}>Закрыть</button>
              <button className="btn-primary" onClick={handleEditSave} disabled={editSaving}>{editSaving&&<Spinner/>}Сохранить</button>
            </div>
            {/* Danger zone inside detail */}
            <DangerZone>
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div><p className="text-sm font-semibold text-red-800">Удалить пользователя</p><p className="text-xs text-red-600">Физическое удаление. Данные будут потеряны навсегда.</p></div>
                  <button className="btn-danger" onClick={()=>{setDetailUser(null);setConfirmUser(detailUser);setConfirmAction("delete");}}><Trash2 className="h-4 w-4"/>Удалить</button>
                </div>
              </div>
            </DangerZone>
          </div>
        )}
      </Modal>

      {/* Role assignment modal */}
      <Modal open={!!roleUser} onClose={()=>setRoleUser(null)} title={`Роли: ${roleUser?.email}`}>
        {roleSaving&&!userRoleIds.length ? <div className="flex justify-center py-8"><Spinner className="h-6 w-6 text-blue-600"/></div> : (
          <div className="space-y-3 mb-6">
            {roles.map(role=>(
              <label key={role.id} className="flex items-start gap-3 rounded-lg border border-gray-200 p-3 cursor-pointer hover:bg-gray-50">
                <input type="checkbox" className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600"
                  checked={userRoleIds.includes(role.id)}
                  onChange={e=>setUserRoleIds(p=>e.target.checked?[...p,role.id]:p.filter(id=>id!==role.id))}/>
                <div>
                  <p className="text-sm font-medium text-gray-900">{role.name} {role.is_system&&<span className="badge bg-blue-100 text-blue-600 ml-1">системная</span>}</p>
                  {role.description&&<p className="text-xs text-gray-500">{role.description}</p>}
                </div>
              </label>
            ))}
          </div>
        )}
        <div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={()=>setRoleUser(null)}>Отмена</button>
          <button className="btn-primary" onClick={handleSaveRoles} disabled={roleSaving}>{roleSaving&&<Spinner/>}Назначить</button>
        </div>
      </Modal>

      {/* Set password modal */}
      <Modal open={!!pwUser} onClose={()=>setPwUser(null)} title={`Установить пароль: ${pwUser?.email}`} size="sm">
        <div className="space-y-3 mb-6">
          <p className="text-sm text-gray-500">Задайте новый пароль. Все активные сессии пользователя будут завершены.</p>
          <div><label className="label">Новый пароль</label><input className="input" type="password" value={newPw} onChange={e=>setNewPw(e.target.value)} placeholder="Мин. 8 символов" autoFocus/></div>
        </div>
        <div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={()=>setPwUser(null)}>Отмена</button>
          <button className="btn-primary" onClick={handleSetPassword} disabled={pwSaving||!newPw}>{pwSaving&&<Spinner/>}Установить</button>
        </div>
      </Modal>

      {/* Confirm modal */}
      <ConfirmModal open={!!confirmUser} onClose={()=>setConfirmUser(null)} onConfirm={handleConfirm} loading={actionLoading}
        danger={confirmAction==="deactivate"||confirmAction==="delete"}
        title={{activate:"Активировать?",deactivate:"Деактивировать?",delete:"Удалить пользователя?",logout:"Завершить все сессии?"}[confirmAction]}
        message={{
          activate:`Пользователь ${confirmUser?.email} снова получит доступ.`,
          deactivate:`Пользователь ${confirmUser?.email} потеряет доступ. Все сессии будут завершены.`,
          delete:`Пользователь ${confirmUser?.email} будет удалён безвозвратно. Это действие нельзя отменить.`,
          logout:`Все активные сессии ${confirmUser?.email} будут немедленно завершены.`,
        }[confirmAction]}/>
    </>
  );
}
