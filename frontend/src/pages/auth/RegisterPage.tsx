import { PasswordStrength } from "../../components/ui/PasswordStrength";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Shield } from "lucide-react";
import { authApi } from "../../api/auth";
import { getErrorMessage } from "../../api/client";
import { Alert, Spinner } from "../../components/ui";

export function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({ first_name:"", last_name:"", middle_name:"", email:"", recovery_email:"", password:"", password_repeat:"" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const set = (f: string) => (e: React.ChangeEvent<HTMLInputElement>) => setForm(p=>({...p,[f]:e.target.value}));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      await authApi.register({ ...form, middle_name: form.middle_name||undefined, recovery_email: form.recovery_email||undefined });
      navigate("/login");
    } catch(err) { setError(getErrorMessage(err)); }
    finally { setLoading(false); }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-gray-100 px-4 py-8">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center">
          <div className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600"><Shield className="h-6 w-6 text-white"/></div>
          <h1 className="text-2xl font-bold text-gray-900">Регистрация</h1>
          <p className="mt-1 text-sm text-gray-500">Роль назначается автоматически: <strong>user</strong></p>
        </div>
        <div className="card p-6">
          <form onSubmit={submit} className="space-y-3">
            {error && <Alert type="error" message={error}/>}
            <div className="grid grid-cols-2 gap-3">
              <div><label className="label">Имя *</label><input className="input" value={form.first_name} onChange={set("first_name")} required/></div>
              <div><label className="label">Фамилия *</label><input className="input" value={form.last_name} onChange={set("last_name")} required/></div>
            </div>
            <div><label className="label">Отчество</label><input className="input" value={form.middle_name} onChange={set("middle_name")}/></div>
            <div><label className="label">Email *</label><input className="input" type="email" value={form.email} onChange={set("email")} required/></div>
            <div>
              <label className="label">Email для восстановления</label>
              <input className="input" type="email" value={form.recovery_email} onChange={set("recovery_email")} placeholder="Необязательно"/>
              <p className="mt-1 text-xs text-gray-400">Используется только для сброса пароля</p>
            </div>
            <div><label className="label">Пароль *</label><input className="input" type="password" value={form.password} onChange={set("password")} required placeholder="Мин. 8 симв., буква и цифра"/></div>
            <PasswordStrength password={form.password}/>
            <div><label className="label">Повторите пароль *</label><input className="input" type="password" value={form.password_repeat} onChange={set("password_repeat")} required/></div>
            <button type="submit" className="btn-primary w-full justify-center mt-2" disabled={loading}>{loading&&<Spinner/>}Зарегистрироваться</button>
          </form>
          <p className="mt-4 text-center text-sm text-gray-500">Уже есть аккаунт?{" "}<Link to="/login" className="font-medium text-blue-600">Войти</Link></p>
        </div>
      </div>
    </div>
  );
}
