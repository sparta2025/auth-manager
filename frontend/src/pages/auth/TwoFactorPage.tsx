import { useEffect, useState } from "react";
import { CheckCircle, XCircle } from "lucide-react";
import { apiClient } from "../../api/client";
import { getErrorMessage } from "../../api/client";
import { Alert, Modal, PageLoader, Spinner } from "../../components/ui";
import { PageHeader } from "../../components/layout/AppLayout";
import toast from "react-hot-toast";

interface TOTPStatus { enabled: boolean; }
interface TOTPSetup  { secret: string; qr_code: string; enabled: boolean; }

export function TwoFactorPage() {
  const [status, setStatus]   = useState<TOTPStatus | null>(null);
  const [setup, setSetup]     = useState<TOTPSetup | null>(null);
  const [otp, setOtp]         = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving]   = useState(false);
  const [error, setError]     = useState("");
  const [disableOpen, setDisableOpen] = useState(false);
  const [disableOtp, setDisableOtp]   = useState("");
  const [disabling, setDisabling]     = useState(false);

  const loadStatus = async () => {
    try { const { data } = await apiClient.get<TOTPStatus>("/auth/2fa/status"); setStatus(data); }
    catch { setStatus({ enabled: false }); }
    finally { setLoading(false); }
  };
  useEffect(() => { loadStatus(); }, []);

  const handleSetup = async () => {
    setSaving(true); setError("");
    try { const { data } = await apiClient.post<TOTPSetup>("/auth/2fa/setup"); setSetup(data); }
    catch (err) { setError(getErrorMessage(err)); }
    finally { setSaving(false); }
  };

  const handleEnable = async () => {
    if (otp.length !== 6) { setError("Введите 6-значный код"); return; }
    setSaving(true); setError("");
    try {
      await apiClient.post("/auth/2fa/enable", { otp });
      toast.success("2FA включена!"); setSetup(null); setOtp(""); await loadStatus();
    } catch (err) { setError(getErrorMessage(err)); }
    finally { setSaving(false); }
  };

  const handleDisable = async () => {
    setDisabling(true);
    try {
      await apiClient.post("/auth/2fa/disable", { otp: disableOtp });
      toast.success("2FA отключена"); setDisableOpen(false); setDisableOtp(""); await loadStatus();
    } catch (err) { toast.error(getErrorMessage(err)); }
    finally { setDisabling(false); }
  };

  if (loading) return <PageLoader />;

  return (
    <>
      <PageHeader title="Двухфакторная аутентификация" subtitle="Защита аккаунта через TOTP"
        breadcrumb={["Главная", "2FA"]}/>
      <div className="p-8 max-w-lg space-y-6">
        {/* Status */}
        <div className="card p-5 flex items-center gap-4">
          {status?.enabled
            ? <CheckCircle className="h-10 w-10 text-green-500 shrink-0"/>
            : <XCircle    className="h-10 w-10 text-gray-300 shrink-0"/>}
          <div className="flex-1">
            <p className="font-semibold text-gray-900 dark:text-gray-100">
              2FA {status?.enabled ? "включена" : "отключена"}
            </p>
            <p className="text-sm text-gray-500">
              {status?.enabled ? "Аккаунт защищён одноразовыми кодами." : "Рекомендуем включить для дополнительной защиты."}
            </p>
          </div>
          {status?.enabled
            ? <button className="btn-danger shrink-0" onClick={() => setDisableOpen(true)}>Отключить</button>
            : <button className="btn-primary shrink-0" onClick={handleSetup} disabled={saving}>{saving && <Spinner/>}Настроить</button>
          }
        </div>

        {/* Setup flow */}
        {setup && (
          <div className="card p-6 space-y-5">
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">Настройка аутентификатора</h3>
            <ol className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
              <li className="flex gap-2"><span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs text-white font-bold">1</span>Установите <strong>Google Authenticator</strong> или <strong>Authy</strong>.</li>
              <li className="flex gap-2"><span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs text-white font-bold">2</span>Отсканируйте QR-код или введите ключ вручную.</li>
              <li className="flex gap-2"><span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-blue-600 text-xs text-white font-bold">3</span>Введите 6-значный код для подтверждения.</li>
            </ol>
            <div className="flex justify-center">
              <img src={setup.qr_code} alt="QR" className="h-48 w-48 rounded-lg border border-gray-200 p-2"/>
            </div>
            <div>
              <p className="mb-1 text-xs text-gray-500">Ключ для ручного ввода:</p>
              <code className="block rounded-lg bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 px-3 py-2 text-sm font-mono break-all">{setup.secret}</code>
            </div>
            {error && <Alert type="error" message={error}/>}
            <div>
              <label className="label">Код подтверждения</label>
              <div className="flex gap-2">
                <input className="input text-center text-xl tracking-widest font-mono" value={otp}
                  onChange={e => setOtp(e.target.value.replace(/\D/g,"").slice(0,6))}
                  placeholder="000000" maxLength={6} autoFocus/>
                <button className="btn-primary shrink-0" onClick={handleEnable} disabled={saving||otp.length!==6}>
                  {saving && <Spinner/>}Включить
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="rounded-lg border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 p-4 text-xs text-gray-500 space-y-1">
          <p>🔐 TOTP — стандарт RFC 6238, совместим с Google Authenticator, Authy, Microsoft Authenticator.</p>
          <p>⚠️ Сохраните секретный ключ — потребуется при потере телефона.</p>
        </div>
      </div>

      {/* Disable modal */}
      <Modal open={disableOpen} onClose={() => { setDisableOpen(false); setDisableOtp(""); }}
        title="Отключить 2FA" size="sm">
        <p className="mb-4 text-sm text-gray-600">Введите текущий код из приложения-аутентификатора.</p>
        <input className="input text-center text-xl tracking-widest font-mono mb-4"
          value={disableOtp} onChange={e => setDisableOtp(e.target.value.replace(/\D/g,"").slice(0,6))}
          placeholder="000000" maxLength={6} autoFocus/>
        <div className="flex justify-end gap-2">
          <button className="btn-secondary" onClick={() => setDisableOpen(false)}>Отмена</button>
          <button className="btn-danger" onClick={handleDisable} disabled={disabling||disableOtp.length!==6}>
            {disabling && <Spinner/>}Отключить
          </button>
        </div>
      </Modal>
    </>
  );
}
