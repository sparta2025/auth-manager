import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Shield } from "lucide-react";
import { authApi } from "../../api/auth";
import { getErrorMessage } from "../../api/client";
import { Alert, Spinner } from "../../components/ui";
import toast from "react-hot-toast";

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const token = params.get("token") ?? "";
  const [form, setForm] = useState({ new_password:"", new_password_repeat:"" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      await authApi.resetPassword({ token, ...form });
      toast.success("Пароль изменён. Войдите с новым паролем.");
      navigate("/login");
    } catch(err) { setError(getErrorMessage(err)); }
    finally { setLoading(false); }
  };

  if (!token) return <div className="flex min-h-screen items-center justify-center"><Alert type="error" message="Токен не найден."/></div>;

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-gray-100 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600"><Shield className="h-6 w-6 text-white"/></div>
          <h1 className="text-2xl font-bold text-gray-900">Новый пароль</h1>
        </div>
        <div className="card p-6">
          <form onSubmit={submit} className="space-y-4">
            {error && <Alert type="error" message={error}/>}
            <div><label className="label">Новый пароль</label><input className="input" type="password" value={form.new_password} onChange={e=>setForm(f=>({...f,new_password:e.target.value}))} required autoFocus placeholder="Мин. 8 симв., буква и цифра"/></div>
            <div><label className="label">Повторите пароль</label><input className="input" type="password" value={form.new_password_repeat} onChange={e=>setForm(f=>({...f,new_password_repeat:e.target.value}))} required/></div>
            <button type="submit" className="btn-primary w-full justify-center" disabled={loading}>{loading&&<Spinner/>}Сохранить пароль</button>
          </form>
          <p className="mt-3 text-center text-xs text-gray-400">Все активные сессии будут завершены.</p>
          <Link to="/login" className="mt-3 flex justify-center text-sm text-blue-600">← Войти</Link>
        </div>
      </div>
    </div>
  );
}
