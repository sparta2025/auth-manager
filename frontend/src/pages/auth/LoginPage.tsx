import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Shield } from "lucide-react";
import { useAuth } from "../../store/auth";
import { getErrorMessage } from "../../api/client";
import { Alert, Spinner } from "../../components/ui";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email:"", password:"" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(""); setLoading(true);
    try { await login(form.email, form.password); navigate("/dashboard"); }
    catch (err) { setError(getErrorMessage(err)); }
    finally { setLoading(false); }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-gray-100 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center">
          <div className="mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600 shadow-lg">
            <Shield className="h-7 w-7 text-white"/>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Auth Manager</h1>
          <p className="mt-1 text-sm text-gray-500">Система управления доступом</p>
        </div>
        <div className="card p-6">
          <form onSubmit={submit} className="space-y-4">
            {error && <Alert type="error" message={error}/>}
            <div><label className="label">Email</label><input className="input" type="email" autoFocus value={form.email} onChange={e=>setForm(f=>({...f,email:e.target.value}))} required/></div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="label mb-0">Пароль</label>
                <Link to="/forgot-password" className="text-xs text-blue-600 hover:text-blue-700">Забыли пароль?</Link>
              </div>
              <input className="input" type="password" value={form.password} onChange={e=>setForm(f=>({...f,password:e.target.value}))} required/>
            </div>
            <button type="submit" className="btn-primary w-full justify-center" disabled={loading}>{loading&&<Spinner/>}Войти</button>
          </form>
          <p className="mt-4 text-center text-sm text-gray-500">Нет аккаунта?{" "}<Link to="/register" className="font-medium text-blue-600 hover:text-blue-700">Зарегистрироваться</Link></p>
        </div>
        <div className="mt-4 rounded-lg border border-blue-100 bg-blue-50 px-4 py-3 text-xs text-blue-700">
          <p className="font-semibold mb-1">Тестовые аккаунты:</p>
          <p>admin@example.com / Admin1234!</p>
          <p>manager@example.com / Manager1234!</p>
          <p>user@example.com / User1234!</p>
        </div>
      </div>
    </div>
  );
}
