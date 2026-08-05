import { useState } from "react";
import { Link, useSearchParams, useNavigate } from "react-router-dom";
import { Mail, Lock, ArrowRight } from "lucide-react";
import { AuthShell, Field } from "@/pages/Login";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";

export function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/auth/forgot-password", { email });
      setSent(true);
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  return (
    <AuthShell title="Recuperar senha" subtitle="Enviaremos instruções para o seu e-mail.">
      {sent ? (
        <div className="text-center text-gray-300">
          <p>Se o e-mail existir, você receberá as instruções em instantes.</p>
          <Link to="/login" className="inline-block mt-6 text-[#FFC107] font-semibold">Voltar ao login</Link>
        </div>
      ) : (
        <form onSubmit={submit} className="space-y-4">
          <Field icon={Mail} type="email" placeholder="E-mail" value={email} onChange={setEmail} testid="forgot-email" />
          <button className="w-full bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full py-3.5 hover:bg-[#e0a800] transition-colors flex items-center justify-center gap-2">
            Enviar <ArrowRight size={18} />
          </button>
          <p className="text-center text-sm text-gray-400"><Link to="/login" className="text-[#FFC107]">Voltar</Link></p>
        </form>
      )}
    </AuthShell>
  );
}

export function ResetPassword() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const token = params.get("token");
  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/auth/reset-password", { token, password });
      toast.success("Senha redefinida! Faça login.");
      navigate("/login");
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  return (
    <AuthShell title="Nova senha" subtitle="Defina sua nova senha de acesso.">
      <form onSubmit={submit} className="space-y-4">
        <Field icon={Lock} type="password" placeholder="Nova senha" value={password} onChange={setPassword} testid="reset-password" />
        <button className="w-full bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full py-3.5 flex items-center justify-center gap-2">
          Redefinir <ArrowRight size={18} />
        </button>
      </form>
    </AuthShell>
  );
}
