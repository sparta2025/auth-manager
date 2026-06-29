import { useCallback, useEffect, useState } from "react";
import { Plus, Pencil, Trash2, FolderOpen } from "lucide-react";
import { documentsApi } from "../../api/resources";
import { getErrorMessage } from "../../api/client";
import { useAuth } from "../../store/auth";
import type { Document } from "../../types";
import { ConfirmModal, EmptyState, Modal, PageLoader, Spinner, Table } from "../../components/ui";
import { PageHeader } from "../../components/layout/AppLayout";
import toast from "react-hot-toast";

export function DocumentsPage() {
  const { hasPermission } = useAuth();
  const canCreate = hasPermission("documents:create");
  const canEdit   = hasPermission("documents:update");
  const canDelete = hasPermission("documents:delete");
  const [docs, setDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editDoc, setEditDoc] = useState<Document|null>(null);
  const [form, setForm] = useState({name:"",body:""});
  const [saving, setSaving] = useState(false);
  const [deleteDoc, setDeleteDoc] = useState<Document|null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async()=>{ setLoading(true); try { setDocs(await documentsApi.getAll()); } catch(err) { toast.error(getErrorMessage(err)); } finally { setLoading(false); } },[]);
  useEffect(()=>{load();},[load]);

  const openCreate = ()=>{ setEditDoc(null); setForm({name:"",body:""}); setModalOpen(true); };
  const openEdit   = (d:Document)=>{ setEditDoc(d); setForm({name:d.name,body:d.body}); setModalOpen(true); };
  const handleSave = async()=>{ setSaving(true); try { editDoc ? await documentsApi.update(editDoc.id,form) : await documentsApi.create(form); toast.success(editDoc?"Обновлён":"Создан"); setModalOpen(false); await load(); } catch(err) { toast.error(getErrorMessage(err)); } finally { setSaving(false); } };
  const handleDelete = async()=>{ if(!deleteDoc) return; setDeleting(true); try { await documentsApi.delete(deleteDoc.id); toast.success("Удалён"); setDeleteDoc(null); await load(); } catch(err) { toast.error(getErrorMessage(err)); } finally { setDeleting(false); } };

  if (loading) return <PageLoader/>;
  return (
    <>
      <PageHeader title="Документы" subtitle={`Всего: ${docs.length}`} breadcrumb={["Ресурсы","Документы"]}
        action={canCreate&&<button className="btn-primary" onClick={openCreate}><Plus className="h-4 w-4"/>Создать</button>}/>
      <div className="p-8">
        {docs.length===0 ? <EmptyState icon={<FolderOpen className="h-12 w-12"/>} title="Нет документов" action={canCreate&&<button className="btn-primary" onClick={openCreate}><Plus className="h-4 w-4"/>Создать</button>}/> : (
          <Table headers={["Название","Содержимое","Действия"]}>
            {docs.map(d=>(
              <tr key={d.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{d.name}</td>
                <td className="px-4 py-3 text-gray-500 text-sm max-w-sm truncate">{d.body}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    {canEdit&&<button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100" onClick={()=>openEdit(d)}><Pencil className="h-3.5 w-3.5"/>Изменить</button>}
                    {canDelete&&<button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50" onClick={()=>setDeleteDoc(d)}><Trash2 className="h-3.5 w-3.5"/>Удалить</button>}
                    {!canEdit&&!canDelete&&<span className="text-xs text-gray-300">только просмотр</span>}
                  </div>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </div>
      <Modal open={modalOpen} onClose={()=>setModalOpen(false)} title={editDoc?"Редактировать документ":"Создать документ"}>
        <div className="space-y-4 mb-6">
          <div><label className="label">Название *</label><input className="input" value={form.name} onChange={e=>setForm(f=>({...f,name:e.target.value}))} autoFocus/></div>
          <div><label className="label">Содержимое *</label><textarea className="input min-h-[120px] resize-y" value={form.body} onChange={e=>setForm(f=>({...f,body:e.target.value}))}/></div>
        </div>
        <div className="flex justify-end gap-2"><button className="btn-secondary" onClick={()=>setModalOpen(false)}>Отмена</button><button className="btn-primary" onClick={handleSave} disabled={saving||!form.name||!form.body}>{saving&&<Spinner/>}{editDoc?"Сохранить":"Создать"}</button></div>
      </Modal>
      <ConfirmModal open={!!deleteDoc} onClose={()=>setDeleteDoc(null)} onConfirm={handleDelete} title="Удалить документ?" danger loading={deleting} message={`Документ «${deleteDoc?.name}» будет удалён.`}/>
    </>
  );
}
