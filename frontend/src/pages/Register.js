import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { User, Mail, Lock, ArrowRight, Loader2, CreditCard } from "lucide-react";
import { AuthShell, Field } from "@/pages/Login";
import { useAuth } from "@/context/AuthContext";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { useCepAutofill, maskCep } from "@/lib/cep";
import { maskCpf, normalizeCpf } from "@/lib/cpf";

const UFS = ["AC","AL","AP","AM","BA","CE","DF","ES","GO","MA","MT","MS","MG","PA","PB","PR","PE","PI","RJ","RN","RS","RO","RR","SC","SP","SE","TO"];

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", cpf: "", newsletter: true });
  const [addr, setAddr] = useState({ zip: "", street: "", number: "", complement: "", district: "", city: "", state: "" });
  const [cepLoading, setCepLoading] = useState(false);
  const [cepError, setCepError] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const cepAutofill = useCepAutofill(
    (data) => {
      setAddr((a) => ({ ...a, street: data.street || a.street, district: data.district || a.district, city: data.city || a.city, state: data.uf || a.state }));
      setCepLoading(false);
      setCepError("");
    },
    { onStart: () => { setCepLoading(true); setCepError(""); }, onError: () => { setCepLoading(false); setCepError("CEP não encontrado. Preencha manualmente."); } }
  );

  const onCep = (v) => {
    const masked = maskCep(v);
    setAddr((a) => ({ ...a, zip: masked }));
    cepAutofill(v);
  };

  const hasAddress = () => addr.zip.replace(/\D/g, "").length === 8 && addr.street.trim() && addr.city.trim();

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    if (hasAddress() && !addr.number.trim()) {
      setError("Informe o número do endereço.");
      return;
    }
    setLoading(true);
    try {
      await register({ ...form, cpf: normalizeCpf(form.cpf) });
      if (hasAddress()) {
        try {
          await api.post("/account/addresses", {
            label: "Principal", recipient: form.name, zip: addr.zip,
            street: addr.street, number: addr.number, complement: addr.complement,
            district: addr.district, city: addr.city, state: addr.state, is_default: true,
          });
        } catch { toast.warning("Conta criada! Mas não conseguimos salvar o endereço — adicione em Minha Conta."); }
      }
      navigate("/conta");
    } catch (err) {
      setError(formatApiError(err.response?.data?.detail) || err.message);
    } finally {
      setLoading(false);
    }
  };

  const inputCls = "w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]";

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
        <Field icon={CreditCard} placeholder="CPF" value={form.cpf} onChange={(v) => setForm({ ...form, cpf: maskCpf(v) })} testid="register-cpf" />

        <div className="pt-2 border-t border-[#2e2e2e]">
          <p className="text-xs uppercase tracking-widest text-[#FFC107] font-bold mt-3 mb-3">Endereço (opcional)</p>
          <div className="grid grid-cols-2 gap-3">
            <div className="relative col-span-2 sm:col-span-1">
              <input data-testid="reg-addr-zip" placeholder="CEP" value={addr.zip} onChange={(e) => onCep(e.target.value)} className={inputCls} inputMode="numeric" />
              {cepLoading && <Loader2 size={16} className="absolute right-3 top-3 animate-spin text-[#FFC107]" data-testid="reg-cep-loading" />}
            </div>
            <input data-testid="reg-addr-street" placeholder="Logradouro" value={addr.street} onChange={(e) => setAddr({ ...addr, street: e.target.value })} className={`${inputCls} col-span-2 sm:col-span-1`} />
            <input data-testid="reg-addr-number" placeholder="Número" value={addr.number} onChange={(e) => setAddr({ ...addr, number: e.target.value })} className={inputCls} />
            <input data-testid="reg-addr-complement" placeholder="Complemento (opcional)" value={addr.complement} onChange={(e) => setAddr({ ...addr, complement: e.target.value })} className={inputCls} />
            <input data-testid="reg-addr-district" placeholder="Bairro" value={addr.district} onChange={(e) => setAddr({ ...addr, district: e.target.value })} className={inputCls} />
            <input data-testid="reg-addr-city" placeholder="Cidade" value={addr.city} onChange={(e) => setAddr({ ...addr, city: e.target.value })} className={inputCls} />
            <select data-testid="reg-addr-state" value={addr.state} onChange={(e) => setAddr({ ...addr, state: e.target.value })} className={`${inputCls} col-span-2`}>
              <option value="">UF</option>
              {UFS.map((uf) => <option key={uf} value={uf}>{uf}</option>)}
            </select>
          </div>
          {cepError && <p data-testid="reg-cep-error" className="text-xs text-[#FFC107] mt-2">{cepError}</p>}
        </div>

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
