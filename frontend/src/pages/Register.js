import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { User, Mail, Lock, ArrowRight } from "lucide-react";
import { AuthShell, Field } from "@/pages/Login";
import { useAuth } from "@/context/AuthContext";
import { formatApiError } from "@/lib/api";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", newsletter: true });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form);
      navigate("/conta");
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthShell title="Criar conta" subtitle="Junte-se ao clube dos colecionadores.">
      <form onSubmit={submit} className="space-y-4">
        {error && (
          <div data-testid="register-error" className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg p-3">
            {error}
          </div>
        )}
        <Field icon={User} placeholder="Nome completo" value={form.name} onChange={(v) => setForm({ ...form, name: v })} testid="register-name" />
        <Field icon={Mail} type="email" placeholder="E-mail" value={form.email} onChange={(v) => setForm({ ...form, email: v })} testid="register-email" />
        <Field icon={Lock} type="password" placeholder="Senha (mín. 6 caracteres)" value={form.password} onChange={(v) => setForm({ ...form, password: v })} testid="register-password" />
        <label className="flex items-center gap-2 text-sm text-gray-400">
          <input type="checkbox" checked={form.newsletter} onChange={(e) => setForm({ ...form, newsletter: e.target.checked })} className="accent-[#FFC107]" />
          Quero receber novidades e promoções
        </label>
        <button data-testid="register-submit" disabled={loading} className="w-full bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full py-3.5 hover:bg-[#e0a800] transition-colors disabled:opacity-50 flex items-center justify-center gap-2">
          {loading ? "Criando..." : <>Criar conta <ArrowRight size={18} /></>}
        </button>
      </form>
      <p className="text-center text-sm text-gray-400 mt-6">
        Já tem conta? <Link to="/login" className="text-[#FFC107] font-semibold">Entrar</Link>
      </p>
    </AuthShell>
  );
}
