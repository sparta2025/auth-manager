import { useCallback, useEffect, useState } from "react";
import { Plus, Pencil, Trash2, FileText } from "lucide-react";
import { reportsApi } from "../../api/resources";
import { getErrorMessage } from "../../api/client";
import { useAuth } from "../../store/auth";
import type { Report } from "../../types";
import { ConfirmModal, EmptyState, Modal, PageLoader, Spinner, Table } from "../../components/ui";
import { PageHeader } from "../../components/layout/AppLayout";
import toast from "react-hot-toast";

export function ReportsPage() {
  const { hasPermission } = useAuth();
  const canCreate = hasPermission("reports:create");
  const canEdit   = hasPermission("reports:update");
  const canDelete = hasPermission("reports:delete");
  const [reports, setReports] = useState<Report[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editReport, setEditReport] = useState<Report|null>(null);
  const [form, setForm] = useState({title:"",content:""});
  const [saving, setSaving] = useState(false);
  const [deleteReport, setDeleteReport] = useState<Report|null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async()=>{ setLoading(true); try { setReports(await reportsApi.getAll()); } catch(err) { toast.error(getErrorMessage(err)); } finally { setLoading(false); } },[]);
  useEffect(()=>{load();},[load]);

  const openCreate = ()=>{ setEditReport(null); setForm({title:"",content:""}); setModalOpen(true); };
  const openEdit   = (r:Report)=>{ setEditReport(r); setForm({title:r.title,content:r.content}); setModalOpen(true); };

  const handleSave = async()=>{ setSaving(true); try { editReport ? await reportsApi.update(editReport.id,form) : await reportsApi.create(form); toast.success(editReport?"Обновлён":"Создан"); setModalOpen(false); await load(); } catch(err) { toast.error(getErrorMessage(err)); } finally { setSaving(false); } };
  const handleDelete = async()=>{ if(!deleteReport) return; setDeleting(true); try { await reportsApi.delete(deleteReport.id); toast.success("Удалён"); setDeleteReport(null); await load(); } catch(err) { toast.error(getErrorMessage(err)); } finally { setDeleting(false); } };

  if (loading) return <PageLoader/>;
  return (
    <>
      <PageHeader title="Отчёты" subtitle={`Всего: ${reports.length}`} breadcrumb={["Ресурсы","Отчёты"]}
        action={canCreate&&<button className="btn-primary" onClick={openCreate}><Plus className="h-4 w-4"/>Создать</button>}/>
      <div className="p-8">
        {reports.length===0 ? <EmptyState icon={<FileText className="h-12 w-12"/>} title="Нет отчётов" action={canCreate&&<button className="btn-primary" onClick={openCreate}><Plus className="h-4 w-4"/>Создать</button>}/> : (
          <Table headers={["Название","Содержимое","Действия"]}>
            {reports.map(r=>(
              <tr key={r.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 font-medium text-gray-900">{r.title}</td>
                <td className="px-4 py-3 text-gray-500 text-sm max-w-sm truncate">{r.content}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    {canEdit&&<button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-gray-600 hover:bg-gray-100" onClick={()=>openEdit(r)}><Pencil className="h-3.5 w-3.5"/>Изменить</button>}
                    {canDelete&&<button className="inline-flex items-center gap-1 rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50" onClick={()=>setDeleteReport(r)}><Trash2 className="h-3.5 w-3.5"/>Удалить</button>}
                    {!canEdit&&!canDelete&&<span className="text-xs text-gray-300">только просмотр</span>}
                  </div>
                </td>
              </tr>
            ))}
          </Table>
        )}
      </div>
      <Modal open={modalOpen} onClose={()=>setModalOpen(false)} title={editReport?"Редактировать отчёт":"Создать отчёт"}>
        <div className="space-y-4 mb-6">
          <div><label className="label">Название *</label><input className="input" value={form.title} onChange={e=>setForm(f=>({...f,title:e.target.value}))} autoFocus/></div>
          <div><label className="label">Содержимое *</label><textarea className="input min-h-[120px] resize-y" value={form.content} onChange={e=>setForm(f=>({...f,content:e.target.value}))}/></div>
        </div>
        <div className="flex justify-end gap-2"><button className="btn-secondary" onClick={()=>setModalOpen(false)}>Отмена</button><button className="btn-primary" onClick={handleSave} disabled={saving||!form.title||!form.content}>{saving&&<Spinner/>}{editReport?"Сохранить":"Создать"}</button></div>
      </Modal>
      <ConfirmModal open={!!deleteReport} onClose={()=>setDeleteReport(null)} onConfirm={handleDelete} title="Удалить отчёт?" danger loading={deleting} message={`Отчёт «${deleteReport?.title}» будет удалён.`}/>
    </>
  );
}
