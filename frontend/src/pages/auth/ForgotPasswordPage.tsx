import { useState } from "react";
import { Link } from "react-router-dom";
import { Shield, ArrowLeft } from "lucide-react";
import { authApi } from "../../api/auth";
import { getErrorMessage } from "../../api/client";
import { Alert, Spinner } from "../../components/ui";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(""); setLoading(true);
    try { await authApi.forgotPassword(email); setSent(true); }
    catch(err) { setError(getErrorMessage(err)); }
    finally { setLoading(false); }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-gray-100 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600"><Shield className="h-6 w-6 text-white"/></div>
          <h1 className="text-2xl font-bold text-gray-900">Восстановление пароля</h1>
        </div>
        <div className="card p-6">
          {sent ? (
            <div className="text-center">
              <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-2xl">✉️</div>
              <h3 className="font-semibold text-gray-900 mb-2">Письмо отправлено</h3>
              <p className="text-sm text-gray-500">Проверьте почту (основную или резервную). Ссылка действует 60 минут.</p>
              <Link to="/login" className="btn-primary mt-4 inline-flex justify-center w-full"><ArrowLeft className="h-4 w-4"/>Вернуться к входу</Link>
            </div>
          ) : (
            <form onSubmit={submit} className="space-y-4">
              {error && <Alert type="error" message={error}/>}
              <p className="text-sm text-gray-500">Укажите email аккаунта. Ссылка для сброса придёт на резервный email (если указан) или на основной.</p>
              <div><label className="label">Email аккаунта</label><input className="input" type="email" value={email} onChange={e=>setEmail(e.target.value)} required autoFocus/></div>
              <button type="submit" className="btn-primary w-full justify-center" disabled={loading}>{loading&&<Spinner/>}Отправить ссылку</button>
              <Link to="/login" className="flex items-center justify-center gap-1 text-sm text-gray-500 hover:text-gray-700 mt-2"><ArrowLeft className="h-3.5 w-3.5"/>Назад</Link>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
