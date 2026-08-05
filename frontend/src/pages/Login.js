import { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { Mail, Lock, ArrowRight } from "lucide-react";
import { LOGO_EMBLEM } from "@/lib/brand";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/lib/api";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(form.email, form.password);
      navigate(location.state?.from || "/conta");
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="Entrar" subtitle="Bem-vindo de volta ao universo Brasil Minis.">
      <form onSubmit={submit} className="space-y-4">
        {error && (
          <div data-testid="login-error" className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg p-3">
            {error}
          </div>
        )}
        <Field icon={Mail} type="email" placeholder="E-mail" value={form.email} onChange={(v) => setForm({ ...form, email: v })} testid="login-email" />
        <Field icon={Lock} type="password" placeholder="Senha" value={form.password} onChange={(v) => setForm({ ...form, password: v })} testid="login-password" />
        <div className="text-right">
          <Link to="/recuperar-senha" className="text-xs text-gray-400 hover:text-[#FFC107]">Esqueci minha senha</Link>
        </div>
        <button data-testid="login-submit" disabled={loading} className="w-full bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full py-3.5 hover:bg-[#e0a800] transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
          {loading ? "Entrando..." : <>Entrar <ArrowRight size={18} /></>}
        </button>
      </form>
      <p className="text-center text-sm text-gray-400 mt-6">
        Não tem conta? <Link to="/cadastro" className="text-[#FFC107] font-semibold">Cadastre-se</Link>
      </p>
    </AuthShell>
  );
}

export function AuthShell({ title, subtitle, children }) {
  return (
    <div className="min-h-[80vh] grid place-items-center px-4 py-12">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <img src={LOGO_EMBLEM} alt="Brasil Minis" className="h-16 w-16 mx-auto rounded-xl object-cover" />
          <h1 className="text-3xl font-display font-black uppercase text-white mt-4">{title}</h1>
          <p className="text-gray-500 mt-2 text-sm">{subtitle}</p>
        </div>
        <div className="bm-card p-8">{children}</div>
      </div>
    </div>
  );
}

export function Field({ icon: Icon, type = "text", placeholder, value, onChange, testid }) {
  return (
    <div className="relative">
      {Icon && <Icon className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500" size={18} />}
      <input
        type={type}
        required
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        data-testid={testid}
        className="w-full bg-[#111111] border border-[#2e2e2e] rounded-full py-3.5 pl-12 pr-4 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-[#1E3A8A] transition-colors"
      />
    </div>
  );
}
