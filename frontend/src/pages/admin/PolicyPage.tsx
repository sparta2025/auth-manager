/**
 * Страница управления политикой паролей (только администратор).
 * Правило security.md: политика применяется и на сервере.
 */
import { useEffect, useState } from "react";
import { Shield, Save, Info } from "lucide-react";
import { apiClient } from "../../api/client";
import { getErrorMessage } from "../../api/client";
import { Alert, PageLoader, Spinner } from "../../components/ui";
import { PageHeader } from "../../components/layout/AppLayout";
import toast from "react-hot-toast";

interface Policy {
  min_length:       number;
  require_digit:    boolean;
  require_letter:   boolean;
  require_upper:    boolean;
  require_special:  boolean;
  expire_days:      number;
}

export function PolicyPage() {
  const [policy, setPolicy]   = useState<Policy | null>(null);
  const [form,   setForm]     = useState<Policy | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving,  setSaving]  = useState(false);
  const [error,   setError]   = useState("");

  useEffect(() => {
    apiClient.get<Policy>("/auth/password-policy")
      .then(r => { setPolicy(r.data); setForm(r.data); })
      .catch(e => setError(getErrorMessage(e)))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    if (!form) return;
    setSaving(true); setError("");
    try {
      const { data } = await apiClient.put<Policy>("/admin/policy", {
        min_length:      form.min_length,
        require_upper:   form.require_upper,
        require_special: form.require_special,
        expire_days:     form.expire_days,
      });
      setPolicy(data); setForm(data);
      toast.success("Политика обновлена");
    } catch (e) { setError(getErrorMessage(e)); }
    finally { setSaving(false); }
  };

  const isDirty = JSON.stringify(form) !== JSON.stringify(policy);

  if (loading) return <PageLoader />;

  return (
    <>
      <PageHeader
        title="Политика паролей"
        subtitle="Требования к паролям всех пользователей"
        breadcrumb={["Администрирование", "Политика паролей"]}
        action={
          <button className="btn-primary" onClick={handleSave}
            disabled={saving || !isDirty}>
            {saving ? <Spinner /> : <Save className="h-4 w-4" />}
            Сохранить
          </button>
        }
      />
      <div className="p-8 max-w-2xl space-y-6">
        {error && <Alert type="error" message={error} />}

        <div className="card p-6 space-y-5">
          <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
            <Shield className="h-4 w-4 text-blue-500" />
            Требования к паролю
          </h3>

          {/* Min length */}
          <div>
            <label className="label">
              Минимальная длина пароля: <strong>{form?.min_length}</strong> символов
            </label>
            <input
              type="range" min={4} max={32}
              value={form?.min_length ?? 8}
              onChange={e => setForm(f => f ? { ...f, min_length: +e.target.value } : f)}
              className="w-full accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>4 (минимум)</span><span>32 (максимум)</span>
            </div>
          </div>

          {/* Checkboxes */}
          {[
            { key: "require_upper",   label: "Требовать заглавную букву (A-Z)" },
            { key: "require_special", label: "Требовать спецсимвол (!@#$%^&*)" },
          ].map(({ key, label }) => (
            <label key={key} className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                checked={form?.[key as keyof Policy] as boolean ?? false}
                onChange={e => setForm(f => f ? { ...f, [key]: e.target.checked } : f)}
              />
              <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
            </label>
          ))}

          {/* Password expiry */}
          <div>
            <label className="label">
              Срок действия пароля (дни):
              <strong className="ml-1">
                {form?.expire_days === 0 ? "без ограничений" : `${form?.expire_days} дней`}
              </strong>
            </label>
            <input
              type="range" min={0} max={365}
              value={form?.expire_days ?? 0}
              onChange={e => setForm(f => f ? { ...f, expire_days: +e.target.value } : f)}
              className="w-full accent-blue-600"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>0 (без ограничений)</span><span>365 дней</span>
            </div>
          </div>

          {/* Fixed rules info */}
          <div className="rounded-lg border border-blue-100 dark:border-blue-900 bg-blue-50 dark:bg-blue-900/20 p-3">
            <p className="flex items-center gap-1.5 text-xs font-semibold text-blue-700 dark:text-blue-300 mb-1">
              <Info className="h-3.5 w-3.5" /> Фиксированные требования (всегда включены)
            </p>
            <ul className="text-xs text-blue-600 dark:text-blue-400 space-y-0.5">
              <li>✓ Минимум одна буква (a-z или A-Z)</li>
              <li>✓ Минимум одна цифра (0-9)</li>
            </ul>
          </div>

          {isDirty && (
            <Alert type="warning" message="Есть несохранённые изменения. Новая политика применяется только к новым паролям." />
          )}
        </div>

        {/* Current preview */}
        <div className="card p-5">
          <h3 className="mb-3 text-sm font-semibold text-gray-700 dark:text-gray-300">
            Предпросмотр требований
          </h3>
          <ul className="space-y-1.5 text-sm text-gray-600 dark:text-gray-400">
            <li className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              Минимум {form?.min_length} символов
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              Содержит букву (обязательно)
            </li>
            <li className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              Содержит цифру (обязательно)
            </li>
            {form?.require_upper && (
              <li className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                Содержит заглавную букву
              </li>
            )}
            {form?.require_special && (
              <li className="flex items-center gap-2">
                <span className="text-green-500">✓</span>
                Содержит спецсимвол
              </li>
            )}
            {(form?.expire_days ?? 0) > 0 && (
              <li className="flex items-center gap-2">
                <span className="text-amber-500">⏱</span>
                Срок действия: {form?.expire_days} дней
              </li>
            )}
          </ul>
        </div>
      </div>
    </>
  );
}
