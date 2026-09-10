import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Eye, Save, Construction, CheckCircle2 } from "lucide-react";
import api, { formatApiError } from "@/lib/api";

const EMPTY = {
  maintenance_enabled: false,
  maintenance_title: "Estamos preparando algo incrível",
  maintenance_subtitle: "",
  maintenance_message: "",
  launch_date: null,
  show_countdown: false,
  whatsapp_url: "",
  instagram_url: "",
  show_whatsapp: false,
  show_instagram: false,
};

// ISO <-> valor do input datetime-local (YYYY-MM-DDTHH:MM)
const toInput = (iso) => (iso ? String(iso).slice(0, 16) : "");
const fromInput = (v) => (v ? new Date(v).toISOString() : null);

const Field = ({ label, children }) => (
  <div className="mb-4">
    <label className="block text-xs uppercase tracking-wide text-gray-400 mb-1.5">{label}</label>
    {children}
  </div>
);

const inputCls = "w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:border-[#FFC107] outline-none";

export default function AdminSite() {
  const [form, setForm] = useState(EMPTY);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get("/admin/site-settings")
      .then((r) => setForm({ ...EMPTY, ...r.data, whatsapp_url: r.data.whatsapp_url || "", instagram_url: r.data.instagram_url || "" }))
      .catch((e) => toast.error(formatApiError(e.response?.data?.detail)))
      .finally(() => setLoading(false));
  }, []);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const toggleMaintenance = () => {
    const next = !form.maintenance_enabled;
    if (next) {
      const ok = window.confirm(
        "Ativar o modo SITE EM CONSTRUÇÃO?\n\nEnquanto ativo, visitantes verão a página de construção. Seu acesso administrativo (login e /admin) continuará funcionando normalmente."
      );
      if (!ok) return;
    }
    set("maintenance_enabled", next);
  };

  const save = async () => {
    setSaving(true);
    try {
      const payload = {
        ...form,
        launch_date: form.launch_date || null,
        whatsapp_url: form.whatsapp_url?.trim() || null,
        instagram_url: form.instagram_url?.trim() || null,
      };
      const { data } = await api.put("/admin/site-settings", payload);
      setForm({ ...EMPTY, ...data, whatsapp_url: data.whatsapp_url || "", instagram_url: data.instagram_url || "" });
      toast.success("Alterações salvas — efeito imediato para novos visitantes.");
    } catch (e) {
      toast.error(formatApiError(e.response?.data?.detail));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="min-h-[50vh] grid place-items-center"><div className="h-10 w-10 rounded-full border-2 border-[#2e2e2e] border-t-[#FFC107] animate-spin" /></div>;
  }

  const on = form.maintenance_enabled;

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6 gap-4 flex-wrap">
        <h1 className="text-3xl font-display font-black uppercase text-white">Site em Construção</h1>
        <a href="/em-construcao?preview=1" target="_blank" rel="noopener noreferrer"
           data-testid="site-preview-btn"
           className="inline-flex items-center gap-2 text-sm font-medium text-gray-300 border border-[#2e2e2e] rounded-full px-4 py-2 hover:text-white hover:border-white/30">
          <Eye size={16} /> Visualizar página
        </a>
      </div>

      {/* Status + toggle */}
      <div className="bm-card p-6 mb-6">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-3">
            {on ? <Construction className="text-[#FFC107]" size={28} /> : <CheckCircle2 className="text-[#009B3A]" size={28} />}
            <div>
              <p className="text-xs uppercase tracking-widest text-gray-500">Status do site</p>
              <p className="text-lg font-display font-black text-white" data-testid="site-status-label">
                {on ? "Site em construção" : "Site publicado"}
              </p>
            </div>
          </div>
          <button
            onClick={toggleMaintenance}
            data-testid="maintenance-toggle"
            aria-pressed={on}
            className={`relative w-20 h-10 rounded-full transition-colors shrink-0 ${on ? "bg-[#FFC107]" : "bg-[#2e2e2e]"}`}
          >
            <span className={`absolute top-1 h-8 w-8 rounded-full bg-white transition-all ${on ? "left-11" : "left-1"}`} />
          </button>
        </div>
        <p className="mt-4 text-sm text-gray-400">
          {on
            ? "Modo ATIVO: visitantes veem a página de construção. Seu acesso a /login e /admin continua funcionando."
            : "Ative para exibir a página de construção aos visitantes. Você continuará acessando o painel normalmente."}
        </p>
      </div>

      {/* Conteúdo da página */}
      <div className="bm-card p-6 mb-6">
        <h2 className="text-base md:text-lg font-display font-bold text-white uppercase mb-4">Conteúdo</h2>
        <Field label="Título">
          <input className={inputCls} data-testid="site-title" value={form.maintenance_title} onChange={(e) => set("maintenance_title", e.target.value)} />
        </Field>
        <Field label="Subtítulo">
          <input className={inputCls} data-testid="site-subtitle" value={form.maintenance_subtitle} onChange={(e) => set("maintenance_subtitle", e.target.value)} />
        </Field>
        <Field label="Mensagem principal">
          <textarea rows={3} className={inputCls} data-testid="site-message" value={form.maintenance_message} onChange={(e) => set("maintenance_message", e.target.value)} />
        </Field>
      </div>

      {/* Contagem regressiva */}
      <div className="bm-card p-6 mb-6">
        <h2 className="text-base md:text-lg font-display font-bold text-white uppercase mb-4">Lançamento</h2>
        <Field label="Data prevista de lançamento">
          <input type="datetime-local" className={inputCls} data-testid="site-launch-date"
                 value={toInput(form.launch_date)} onChange={(e) => set("launch_date", fromInput(e.target.value))} />
        </Field>
        <label className="flex items-center gap-2 text-sm text-gray-300">
          <input type="checkbox" className="accent-[#FFC107]" data-testid="site-show-countdown"
                 checked={form.show_countdown} onChange={(e) => set("show_countdown", e.target.checked)} />
          Exibir contagem regressiva
        </label>
      </div>

      {/* Redes sociais */}
      <div className="bm-card p-6 mb-6">
        <h2 className="text-base md:text-lg font-display font-bold text-white uppercase mb-4">Contato & Redes</h2>
        <Field label="URL do WhatsApp (ex.: https://wa.me/55...)">
          <input className={inputCls} data-testid="site-whatsapp-url" value={form.whatsapp_url} onChange={(e) => set("whatsapp_url", e.target.value)} placeholder="https://wa.me/55DDDNUMERO" />
        </Field>
        <label className="flex items-center gap-2 text-sm text-gray-300 mb-4">
          <input type="checkbox" className="accent-[#FFC107]" data-testid="site-show-whatsapp"
                 checked={form.show_whatsapp} onChange={(e) => set("show_whatsapp", e.target.checked)} />
          Exibir botão do WhatsApp
        </label>
        <Field label="URL do Instagram (ex.: https://instagram.com/...)">
          <input className={inputCls} data-testid="site-instagram-url" value={form.instagram_url} onChange={(e) => set("instagram_url", e.target.value)} placeholder="https://instagram.com/brasilminis" />
        </Field>
        <label className="flex items-center gap-2 text-sm text-gray-300">
          <input type="checkbox" className="accent-[#FFC107]" data-testid="site-show-instagram"
                 checked={form.show_instagram} onChange={(e) => set("show_instagram", e.target.checked)} />
          Exibir botão do Instagram
        </label>
      </div>

      <button onClick={save} disabled={saving} data-testid="site-save-btn"
              className="inline-flex items-center gap-2 bg-[#FFC107] text-[#111111] font-bold rounded-full px-6 py-3 disabled:opacity-60">
        <Save size={18} /> {saving ? "Salvando..." : "Salvar alterações"}
      </button>
    </div>
  );
}
