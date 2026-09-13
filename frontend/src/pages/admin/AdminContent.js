import { useEffect, useState } from "react";
import { FileText, Share2, ExternalLink, Save, Eye, Info } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { invalidateSiteContent } from "@/lib/siteContent";
import { useSiteConfig } from "@/context/SiteConfigContext";

const PAGE_TABS = [
  { k: "about", l: "Sobre Nós", route: "/sobre" },
  { k: "contact", l: "Contato", route: "/contato" },
  { k: "returns", l: "Trocas e Devoluções", route: "/trocas-devolucoes" },
  { k: "shipping", l: "Frete e Entrega", route: "/frete-entrega" },
];

const SOCIALS = [
  ["instagram", "Instagram", "https://instagram.com/sualoja"],
  ["facebook", "Facebook", "https://facebook.com/sualoja"],
  ["tiktok", "TikTok", "https://tiktok.com/@sualoja"],
  ["youtube", "YouTube", "https://youtube.com/@sualoja"],
  ["whatsapp", "WhatsApp", "https://wa.me/5511999990000"],
  ["telegram", "Telegram", "https://t.me/sualoja"],
  ["twitter", "X / Twitter", "https://x.com/sualoja"],
  ["pinterest", "Pinterest", "https://pinterest.com/sualoja"],
];

export default function AdminContent() {
  const [tab, setTab] = useState("about");
  const [content, setContent] = useState(null);
  const [social, setSocial] = useState(null);
  const [saving, setSaving] = useState(false);
  const { refresh: refreshConfig } = useSiteConfig();

  useEffect(() => {
    api.get("/admin/site-content").then((r) => setContent(r.data.content)).catch(() => {});
    api.get("/admin/social-links").then((r) => setSocial(r.data.social_links)).catch(() => {});
  }, []);

  const setPageField = (page, key, value) => setContent((c) => ({ ...c, [page]: { ...c[page], [key]: value } }));
  const setSocialField = (plat, key, value) => setSocial((s) => ({ ...s, [plat]: { ...s[plat], [key]: value } }));

  const saveContent = async () => {
    setSaving(true);
    try {
      const { data } = await api.put("/admin/site-content", content);
      setContent(data.content);
      invalidateSiteContent();
      toast.success("Conteúdo salvo com sucesso.");
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setSaving(false); }
  };

  const saveSocial = async () => {
    setSaving(true);
    try {
      const { data } = await api.put("/admin/social-links", social);
      setSocial(data.social_links);
      invalidateSiteContent();
      refreshConfig();
      toast.success("Redes sociais salvas com sucesso.");
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
    finally { setSaving(false); }
  };

  if (!content || !social) return <div className="text-gray-400">Carregando...</div>;

  return (
    <div>
      <div className="flex items-center gap-3 mb-2">
        <FileText className="text-[#FFC107]" size={28} />
        <h1 className="text-3xl font-display font-black uppercase text-white">Conteúdo do Site</h1>
      </div>
      <p className="text-gray-500 text-sm mb-6">Textos institucionais e redes sociais — a fonte da verdade é este painel.</p>

      <div className="flex flex-wrap gap-2 mb-6">
        {PAGE_TABS.map((t) => (
          <button key={t.k} onClick={() => setTab(t.k)} data-testid={`content-tab-${t.k}`}
            className={`px-4 py-2 rounded-full text-sm font-semibold transition-colors ${tab === t.k ? "bg-[#1E3A8A] text-white" : "bg-[#1f1f1f] text-gray-400 hover:text-white"}`}>
            {t.l}
          </button>
        ))}
        <button onClick={() => setTab("social")} data-testid="content-tab-social"
          className={`px-4 py-2 rounded-full text-sm font-semibold flex items-center gap-2 transition-colors ${tab === "social" ? "bg-[#1E3A8A] text-white" : "bg-[#1f1f1f] text-gray-400 hover:text-white"}`}>
          <Share2 size={15} /> Redes Sociais
        </button>
      </div>

      {tab !== "social" ? (
        <PageEditor
          pageKey={tab}
          page={content[tab]}
          route={PAGE_TABS.find((t) => t.k === tab)?.route}
          onChange={(k, v) => setPageField(tab, k, v)}
          onSave={saveContent}
          saving={saving}
        />
      ) : (
        <SocialEditor social={social} onChange={setSocialField} onSave={saveSocial} saving={saving} />
      )}
    </div>
  );
}

function PageEditor({ pageKey, page, route, onChange, onSave, saving }) {
  const isContact = pageKey === "contact";
  return (
    <div className="bm-card p-6 max-w-3xl" data-testid={`page-editor-${pageKey}`}>
      <div className="flex items-center justify-between mb-5">
        <label className="flex items-center gap-2 text-sm font-semibold text-white cursor-pointer">
          <input type="checkbox" checked={!!page.active} onChange={(e) => onChange("active", e.target.checked)} data-testid={`page-${pageKey}-active`} className="accent-[#FFC107] h-4 w-4" />
          Página ativa (visível no site)
        </label>
        <a href={`${window.location.origin}${route}`} target="_blank" rel="noopener noreferrer" data-testid={`page-${pageKey}-preview`} className="text-xs text-[#FFC107] flex items-center gap-1 hover:underline">
          <Eye size={14} /> Visualizar página
        </a>
      </div>

      <div className="space-y-4">
        <Field label="Título" value={page.title} onChange={(v) => onChange("title", v)} testid={`page-${pageKey}-title`} />
        <Field label="Subtítulo (opcional)" value={page.subtitle} onChange={(v) => onChange("subtitle", v)} testid={`page-${pageKey}-subtitle`} />

        {isContact && (
          <div className="border border-[#2e2e2e] rounded-lg p-4">
            <p className="text-xs text-gray-400 mb-3">Marque quais campos de contato aparecem na página. Desmarcar oculta o campo mesmo com valor preenchido.</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <ContactField label="E-mail" fk="email" sk="show_email" page={page} onChange={onChange} />
              <ContactField label="Telefone" fk="phone" sk="show_phone" page={page} onChange={onChange} />
              <ContactField label="WhatsApp (URL https)" fk="whatsapp" sk="show_whatsapp" page={page} onChange={onChange} />
              <ContactField label="Horário de atendimento" fk="hours" sk="show_hours" page={page} onChange={onChange} />
              <ContactField label="Endereço comercial" fk="address" sk="show_address" page={page} onChange={onChange} />
              <ContactField label="Link do mapa (https)" fk="map_url" sk="show_map_url" page={page} onChange={onChange} />
            </div>
          </div>
        )}

        <div>
          <label className="text-xs text-gray-500 block mb-1">Conteúdo principal</label>
          <div className="flex items-start gap-2 text-[11px] text-gray-500 bg-[#111] border border-[#2e2e2e] rounded-lg p-2 mb-2">
            <Info size={13} className="text-[#FFC107] shrink-0 mt-0.5" />
            <span>Formatação simples (Markdown): <b>## Título</b>, <b>**negrito**</b>, listas com <b>-</b>, links <b>[texto](https://...)</b>. HTML inseguro é removido automaticamente.</span>
          </div>
          <textarea value={page.content || ""} onChange={(e) => onChange("content", e.target.value)} rows={12} data-testid={`page-${pageKey}-content`}
            className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white font-mono focus:outline-none focus:border-[#1E3A8A]" />
        </div>

        <div className="grid grid-cols-1 gap-4 pt-2 border-t border-[#2e2e2e]">
          <Field label="SEO Title (opcional)" value={page.seo_title} onChange={(v) => onChange("seo_title", v)} testid={`page-${pageKey}-seo-title`} />
          <Field label="SEO Description (opcional)" value={page.seo_description} onChange={(v) => onChange("seo_description", v)} testid={`page-${pageKey}-seo-desc`} />
        </div>
      </div>

      <button onClick={onSave} disabled={saving} data-testid="save-content-btn" className="mt-6 bg-[#FFC107] text-[#111] font-bold rounded-full px-6 py-3 flex items-center gap-2">
        <Save size={16} /> {saving ? "Salvando..." : "Salvar alterações"}
      </button>
    </div>
  );
}

function SocialEditor({ social, onChange, onSave, saving }) {
  return (
    <div className="bm-card p-6 max-w-3xl" data-testid="social-editor">
      <div className="space-y-3">
        {SOCIALS.map(([key, label, placeholder]) => (
          <div key={key} className="flex items-center gap-3">
            <label className="flex items-center gap-2 w-40 shrink-0 text-sm text-white">
              <input type="checkbox" checked={!!social[key]?.active} onChange={(e) => onChange(key, "active", e.target.checked)} data-testid={`social-${key}-active`} className="accent-[#FFC107] h-4 w-4" />
              {label}
            </label>
            <input value={social[key]?.url || ""} onChange={(e) => onChange(key, "url", e.target.value)} placeholder={placeholder} data-testid={`social-${key}-url`}
              className="flex-1 bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
            {social[key]?.url && (
              <a href={social[key].url} target="_blank" rel="noopener noreferrer" className="text-gray-500 hover:text-[#FFC107]"><ExternalLink size={16} /></a>
            )}
          </div>
        ))}
      </div>
      <p className="text-xs text-gray-500 mt-4">Somente redes com URL preenchida e ativas aparecem no site (footer e página de contato).</p>
      <button onClick={onSave} disabled={saving} data-testid="save-social-btn" className="mt-6 bg-[#FFC107] text-[#111] font-bold rounded-full px-6 py-3 flex items-center gap-2">
        <Save size={16} /> {saving ? "Salvando..." : "Salvar alterações"}
      </button>
    </div>
  );
}

function ContactField({ label, fk, sk, page, onChange }) {
  const shown = page[sk] !== false; // default visível (compat)
  return (
    <div className={`rounded-lg border p-3 transition-colors ${shown ? "border-[#2e2e2e]" : "border-[#2e2e2e] opacity-60"}`}>
      <label className="flex items-center justify-between gap-2 mb-1.5 cursor-pointer">
        <span className="text-xs font-semibold text-white">{label}</span>
        <input type="checkbox" checked={shown} onChange={(e) => onChange(sk, e.target.checked)} data-testid={`page-contact-${fk}-show`} className="accent-[#FFC107] h-4 w-4" />
      </label>
      <input value={page[fk] || ""} onChange={(e) => onChange(fk, e.target.value)} data-testid={`page-contact-${fk}`} disabled={!shown}
        className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-[#1E3A8A] disabled:opacity-50" />
    </div>
  );
}

function Field({ label, value, onChange, testid }) {
  return (
    <div>
      <label className="text-xs text-gray-500 block mb-1">{label}</label>
      <input value={value || ""} onChange={(e) => onChange(e.target.value)} data-testid={testid}
        className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
    </div>
  );
}
