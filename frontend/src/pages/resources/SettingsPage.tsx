import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { settingsApi } from "../../api/resources";
import { useAuth } from "../../store/auth";
import { getErrorMessage } from "../../api/client";
import type { Settings } from "../../types";
import { Alert, PageLoader, Spinner } from "../../components/ui";
import { PageHeader } from "../../components/layout/AppLayout";
import toast from "react-hot-toast";

export function SettingsPage() {
  const { hasPermission } = useAuth();
  const canEdit = hasPermission("settings:update");
  const [settings, setSettings] = useState<Settings|null>(null);
  const [form, setForm] = useState<Settings|null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(()=>{
    settingsApi.get().then(s=>{setSettings(s);setForm(s);}).catch(e=>setError(getErrorMessage(e))).finally(()=>setLoading(false));
  },[]);

  const handleSave = async()=>{ if(!form) return; setSaving(true); setError(""); try { const u=await settingsApi.update(form); setSettings(u); setForm(u); toast.success("Настройки сохранены"); } catch(e) { setError(getErrorMessage(e)); } finally { setSaving(false); } };
  const isDirty = JSON.stringify(form)!==JSON.stringify(settings);

  if (loading) return <PageLoader/>;
  return (
    <>
      <PageHeader title="Настройки системы" subtitle="Параметры приложения" breadcrumb={["Ресурсы","Настройки"]}
        action={canEdit&&<button className="btn-primary" onClick={handleSave} disabled={saving||!isDirty}>{saving?<Spinner/>:<Save className="h-4 w-4"/>}Сохранить</button>}/>
      <div className="p-8 max-w-xl">
        <div className="card p-6 space-y-5">
          {error&&<Alert type="error" message={error}/>}
          {!canEdit&&<Alert type="info" message="Только просмотр. Изменение настроек доступно администраторам."/>}
          <div><label className="label">Название сайта</label><input className="input" value={form?.site_name??""} disabled={!canEdit} onChange={e=>setForm(f=>f?{...f,site_name:e.target.value}:f)}/></div>
          <div><label className="label">Макс. размер загрузки (МБ)</label><input className="input" type="number" min={1} max={1024} value={form?.max_upload_size_mb??10} disabled={!canEdit} onChange={e=>setForm(f=>f?{...f,max_upload_size_mb:parseInt(e.target.value)||10}:f)}/></div>
          <div className="flex items-center justify-between rounded-xl border border-gray-200 p-4">
            <div><p className="text-sm font-medium text-gray-900">Режим обслуживания</p><p className="text-xs text-gray-500 mt-0.5">Ограничивает доступ к системе</p></div>
            <button role="switch" disabled={!canEdit} aria-checked={form?.maintenance_mode}
              onClick={()=>setForm(f=>f?{...f,maintenance_mode:!f.maintenance_mode}:f)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${form?.maintenance_mode?"bg-red-500":"bg-gray-200"} ${!canEdit?"opacity-50 cursor-not-allowed":""}`}>
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${form?.maintenance_mode?"translate-x-6":"translate-x-1"}`}/>
            </button>
          </div>
          {isDirty&&canEdit&&<div className="rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs text-amber-700">Есть несохранённые изменения.</div>}
        </div>
      </div>
    </>
  );
}
