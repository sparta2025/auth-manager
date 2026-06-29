import { useCallback, useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Shield, Key } from "lucide-react";
import { adminApi } from "../../api/admin";
import { getErrorMessage } from "../../api/client";
import type { Permission, Role } from "../../types";
import { ConfirmModal, EmptyState, Modal, PageLoader, Spinner, Table } from "../../components/ui";
import { PageHeader } from "../../components/layout/AppLayout";
import toast from "react-hot-toast";

export function RolesPage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [allPerms, setAllPerms] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editRole, setEditRole] = useState<Role|null>(null);
  const [form, setForm] = useState({ name:"", description:"" });
  const [saving, setSaving] = useState(false);
  const [deleteRole, setDeleteRole] = useState<Role|null>(null);
  const [deleting, setDeleting] = useState(false);
  // Permission assignment
  const [permRole, setPermRole] = useState<Role|null>(null);
  const [selectedPerms, setSelectedPerms] = useState<string[]>([]);
  const [permSaving, setPermSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try { const [r,p]=await Promise.all([adminApi.getRoles(),adminApi.getPermissions()]); setRoles(r); setAllPerms(p); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setLoading(false); }
  }, []);

  useEffect(()=>{load();},[load]);

  const openCreate = () => { setEditRole(null); setForm({name:"",description:""}); setModalOpen(true); };
  const openEdit = (r: Role) => { setEditRole(r); setForm({name:r.name,description:r.description??""}); setModalOpen(true); };

  const handleSave = async () => {
    setSaving(true);
    try {
      if (editRole) { await adminApi.updateRole(editRole.id,{name:form.name,description:form.description||undefined}); toast.success("Роль обновлена"); }
      else { await adminApi.createRole({name:form.name,description:form.description||undefined}); toast.success("Роль создана"); }
      setModalOpen(false); await load();
    } catch(err) { toast.error(getErrorMessage(err)); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    if (!deleteRole) return; setDeleting(true);
    try { await adminApi.deleteRole(deleteRole.id); toast.success("Роль удалена"); setDeleteRole(null); await load(); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setDeleting(false); }
  };

  const openPerms = async (role: Role) => {
    setPermRole(role); setPermSaving(true);
    try { const p = await adminApi.getRolePermissions(role.id); setSelectedPerms(p.map(x=>x.id)); }
    catch { setSelectedPerms([]); }
    finally { setPermSaving(false); }
  };

  const handleSavePerms = async () => {
    if (!permRole) return; setPermSaving(true);
    try { await adminApi.assignPermissionsToRole(permRole.id, selectedPerms); toast.success("Разрешения обновлены"); setPermRole(null); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setPermSaving(false); }
  };

  const grouped = allPerms.reduce<Record<string,Permission[]>>((acc,p)=>{ (acc[p.resource]=acc[p.resource]??[]).push(p); return acc; }, {});
  const actionColor: Record<string,string> = { create:"bg-green-100 text-green-700",read:"bg-blue-100 text-blue-700",update:"bg-amber-100 text-amber-700",delete:"bg-red-100 text-red-700",manage:"bg-violet-100 text-violet-700" };

  if (loading) return <PageLoader/>;

  return (
    <>
      <PageHeader title="Роли" subtitle={`Всего: ${roles.length}`} breadcrumb={["Администрирование","Роли"]}
        action={<button className="btn-primary" onClick={openCreate}><Plus className="h-4 w-4"/>Создать роль</button>}/>
      <div className="p-8">
        {roles.length===0 ? <EmptyState icon={<Shield className="h-12 w-12"/>} title="Нет ролей" action={<button className="btn-primary" onClick={openCreate}><Plus className="h-4 w-4"/>Создать</button>}/> : (
          <Table headers={["Название","Описание","Тип","Действия"]}>
            {roles.map(role=>(
              <tr key={role.id} className="hover:bg-gray-50">
                <td className="px-4 py-3"><div className="flex items-center gap-2"><div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600"><Shield className="h-4 w-4"/></div><span className="font-medium text-gray-900">{role.name}</span></div></td>
                <td className="px-4 py-3 text-gray-500 text-sm">{role.description??<span className="text-gray-300 italic">—</span>}</td>
                <td className="px-4 py-3"><span className={`badge ${role.is_system?"bg-blue-100 text-blue-700":"bg-gray-100 text-gray-600"}`}>{role.is_system?"системная":"пользовательская"}</span></td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-1">
                    <button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-violet-600 hover:bg-violet-50" onClick={()=>openPerms(role)}><Key className="h-3.5 w-3.5"/>Разрешения</button>
                    <button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100" onClick={()=>openEdit(role)}><Pencil className="h-3.5 w-3.5"/>Изменить</button>
                    {!role.is_system&&<button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50" onClick={()=>setDeleteRole(role)}><Trash2 className="h-3.5 w-3.5"/>Удалить</button>}
                  </div>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </div>

      <Modal open={modalOpen} onClose={()=>setModalOpen(false)} title={editRole?"Редактировать роль":"Создать роль"}>
        <div className="space-y-4 mb-6">
          <div><label className="label">Название *</label><input className="input" value={form.name} onChange={e=>setForm(f=>({...f,name:e.target.value}))} autoFocus/></div>
          <div><label className="label">Описание</label><input className="input" value={form.description} onChange={e=>setForm(f=>({...f,description:e.target.value}))}/></div>
        </div>
        <div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={()=>setModalOpen(false)}>Отмена</button>
          <button className="btn-primary" onClick={handleSave} disabled={saving||!form.name.trim()}>{saving&&<Spinner/>}{editRole?"Сохранить":"Создать"}</button>
        </div>
      </Modal>

      {/* Permissions for role */}
      <Modal open={!!permRole} onClose={()=>setPermRole(null)} title={`Разрешения роли: ${permRole?.name}`} size="lg">
        {permSaving&&!selectedPerms.length ? <div className="flex justify-center py-8"><Spinner className="h-6 w-6 text-blue-600"/></div> : (
          <div className="space-y-4 mb-6 max-h-96 overflow-y-auto">
            {Object.entries(grouped).map(([resource,perms])=>(
              <div key={resource}>
                <p className="mb-2 text-xs font-bold uppercase tracking-wide text-gray-400">{resource}</p>
                <div className="grid grid-cols-2 gap-2">
                  {perms.map(p=>(
                    <label key={p.id} className="flex items-center gap-2 rounded-lg border border-gray-100 p-2.5 cursor-pointer hover:bg-gray-50">
                      <input type="checkbox" className="h-4 w-4 rounded border-gray-300 text-blue-600"
                        checked={selectedPerms.includes(p.id)}
                        onChange={e=>setSelectedPerms(prev=>e.target.checked?[...prev,p.id]:prev.filter(id=>id!==p.id))}/>
                      <span className="text-xs font-mono text-gray-700">{p.code}</span>
                      <span className={`ml-auto badge text-xs ${actionColor[p.action]??""}`}>{p.action}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
        <div className="flex justify-end gap-2 border-t border-gray-100 pt-4">
          <button className="btn-secondary" onClick={()=>setPermRole(null)}>Отмена</button>
          <button className="btn-primary" onClick={handleSavePerms} disabled={permSaving}>{permSaving&&<Spinner/>}Сохранить</button>
        </div>
      </Modal>

      <ConfirmModal open={!!deleteRole} onClose={()=>setDeleteRole(null)} onConfirm={handleDelete}
        title="Удалить роль?" danger loading={deleting}
        message={`Роль «${deleteRole?.name}» будет удалена. Все пользователи потеряют эту роль.`}/>
    </>
  );
}
