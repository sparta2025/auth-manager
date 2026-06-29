import { useCallback, useEffect, useState } from "react";
import { Plus, Pencil, Trash2, Key } from "lucide-react";
import { adminApi } from "../../api/admin";
import { getErrorMessage } from "../../api/client";
import type { Permission } from "../../types";
import { ConfirmModal, EmptyState, Modal, PageLoader, Spinner, Table } from "../../components/ui";
import { PageHeader } from "../../components/layout/AppLayout";
import toast from "react-hot-toast";

const RESOURCES = ["users","reports","documents","settings","audit","notifications"];
const ACTIONS   = ["create","read","update","delete","manage"];
const ACTION_COLOR: Record<string,string> = {create:"bg-green-100 text-green-700",read:"bg-blue-100 text-blue-700",update:"bg-amber-100 text-amber-700",delete:"bg-red-100 text-red-700",manage:"bg-violet-100 text-violet-700"};

export function PermissionsPage() {
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [form, setForm] = useState({ resource:"reports", action:"read", custom_resource:"", description:"" });
  const [saving, setSaving] = useState(false);
  const [editPerm, setEditPerm] = useState<Permission|null>(null);
  const [editDesc, setEditDesc] = useState("");
  const [deletePerm, setDeletePerm] = useState<Permission|null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async()=>{
    setLoading(true);
    try { setPermissions(await adminApi.getPermissions()); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setLoading(false); }
  },[]);

  useEffect(()=>{load();},[load]);

  const resource = form.resource==="__custom__" ? form.custom_resource : form.resource;
  const code = `${resource}:${form.action}`;

  const handleCreate = async () => {
    if (!resource) return; setSaving(true);
    try { await adminApi.createPermission({code,resource,action:form.action,description:form.description||undefined}); toast.success("Разрешение создано"); setCreateOpen(false); await load(); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setSaving(false); }
  };

  const handleEditSave = async () => {
    if (!editPerm) return; setSaving(true);
    try { await adminApi.updatePermission(editPerm.id,editDesc); toast.success("Описание обновлено"); setEditPerm(null); await load(); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setSaving(false); }
  };

  const handleDelete = async () => {
    if (!deletePerm) return; setDeleting(true);
    try { await adminApi.deletePermission(deletePerm.id); toast.success("Разрешение удалено"); setDeletePerm(null); await load(); }
    catch(err) { toast.error(getErrorMessage(err)); }
    finally { setDeleting(false); }
  };

  const grouped = permissions.reduce<Record<string,Permission[]>>((acc,p)=>{ (acc[p.resource]=acc[p.resource]??[]).push(p); return acc; },{});

  if (loading) return <PageLoader/>;

  return (
    <>
      <PageHeader title="Разрешения" subtitle={`Всего: ${permissions.length}`} breadcrumb={["Администрирование","Разрешения"]}
        action={<button className="btn-primary" onClick={()=>setCreateOpen(true)}><Plus className="h-4 w-4"/>Создать</button>}/>
      <div className="p-8 space-y-6">
        {permissions.length===0 ? <EmptyState icon={<Key className="h-12 w-12"/>} title="Нет разрешений"/> : (
          Object.entries(grouped).map(([resource,perms])=>(
            <div key={resource}>
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-600 uppercase tracking-wide"><Key className="h-3.5 w-3.5 text-gray-400"/>{resource}</h3>
              <Table headers={["Код","Действие","Описание",""]}>
                {perms.map(p=>(
                  <tr key={p.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-sm text-gray-800">{p.code}</td>
                    <td className="px-4 py-3"><span className={`badge ${ACTION_COLOR[p.action]??"bg-gray-100 text-gray-700"}`}>{p.action}</span></td>
                    <td className="px-4 py-3 text-sm text-gray-500">{p.description??<span className="text-gray-300 italic">—</span>}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-1 justify-end">
                        <button className="rounded p-1.5 text-gray-400 hover:bg-gray-100" onClick={()=>{setEditPerm(p);setEditDesc(p.description??"");}}><Pencil className="h-3.5 w-3.5"/></button>
                        <button className="rounded p-1.5 text-red-400 hover:bg-red-50" onClick={()=>setDeletePerm(p)}><Trash2 className="h-3.5 w-3.5"/></button>
                      </div>
                    </td>
                  </tr>
                ))}
              </Table>
            </div>
          ))
        )}
      </div>

      <Modal open={createOpen} onClose={()=>setCreateOpen(false)} title="Создать разрешение">
        <div className="space-y-4 mb-6">
          <div>
            <label className="label">Ресурс</label>
            <select className="input" value={form.resource} onChange={e=>setForm(f=>({...f,resource:e.target.value}))}>
              {RESOURCES.map(r=><option key={r}>{r}</option>)}
              <option value="__custom__">Другой…</option>
            </select>
            {form.resource==="__custom__"&&<input className="input mt-2" placeholder="Введите ресурс" value={form.custom_resource} onChange={e=>setForm(f=>({...f,custom_resource:e.target.value}))}/>}
          </div>
          <div>
            <label className="label">Действие</label>
            <select className="input" value={form.action} onChange={e=>setForm(f=>({...f,action:e.target.value}))}>
              {ACTIONS.map(a=><option key={a}>{a}</option>)}
            </select>
          </div>
          <div><label className="label">Код (авто)</label><input className="input bg-gray-50 font-mono text-gray-500" value={code} readOnly/></div>
          <div><label className="label">Описание</label><input className="input" value={form.description} onChange={e=>setForm(f=>({...f,description:e.target.value}))}/></div>
        </div>
        <div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={()=>setCreateOpen(false)}>Отмена</button>
          <button className="btn-primary" onClick={handleCreate} disabled={saving||!resource}>{saving&&<Spinner/>}Создать</button>
        </div>
      </Modal>

      <Modal open={!!editPerm} onClose={()=>setEditPerm(null)} title={`Редактировать: ${editPerm?.code}`} size="sm">
        <div className="mb-6"><label className="label">Описание</label><input className="input" value={editDesc} onChange={e=>setEditDesc(e.target.value)} autoFocus/></div>
        <div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={()=>setEditPerm(null)}>Отмена</button>
          <button className="btn-primary" onClick={handleEditSave} disabled={saving}>{saving&&<Spinner/>}Сохранить</button>
        </div>
      </Modal>

      <ConfirmModal open={!!deletePerm} onClose={()=>setDeletePerm(null)} onConfirm={handleDelete}
        title="Удалить разрешение?" danger loading={deleting}
        message={`Разрешение «${deletePerm?.code}» будет удалено из всех ролей.`}/>
    </>
  );
}
