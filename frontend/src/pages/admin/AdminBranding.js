import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { Upload, RotateCcw, Save, Eye, ImageIcon } from "lucide-react";
import api, { formatApiError } from "@/lib/api";
import { useSiteConfig, resolveLogo } from "@/context/SiteConfigContext";

export default function AdminBranding() {
  const { refresh } = useSiteConfig();
  const [cfg, setCfg] = useState({ logo_url: null, logo_width: 200 });
  const [width, setWidth] = useState(200);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef(null);

  const load = () =>
    api.get("/admin/site-config").then((r) => {
      setCfg(r.data);
      setWidth(r.data.logo_width || 200);
    });

  useEffect(() => { load().catch((e) => toast.error(formatApiError(e.response?.data?.detail))).finally(() => setLoading(false)); }, []);

  const onUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("file", file);
      await api.post("/admin/site-config/logo", fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success("Logo enviada com sucesso.");
      await load(); await refresh();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const saveWidth = async () => {
    setBusy(true);
    try {
      await api.put("/admin/site-config", { logo_width: width });
      toast.success("Tamanho salvo.");
      await load(); await refresh();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setBusy(false); }
  };

  const restore = async () => {
    if (!window.confirm("Restaurar a logo padrão do Brasil Minis? A logo enviada será removida.")) return;
    setBusy(true);
    try {
      await api.delete("/admin/site-config/logo");
      toast.success("Logo padrão restaurada.");
      await load(); await refresh();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally { setBusy(false); }
  };

  if (loading) return <div className="min-h-[50vh] grid place-items-center"><div className="h-10 w-10 rounded-full border-2 border-[#2e2e2e] border-t-[#FFC107] animate-spin" /></div>;

  const previewSrc = resolveLogo(cfg.logo_url);

  return (
    <div className="max-w-3xl">
      <div className="flex items-center justify-between mb-6 gap-4 flex-wrap">
        <div>
          <p className="text-xs uppercase tracking-widest text-gray-500">Configurações</p>
          <h1 className="text-3xl font-display font-black uppercase text-white">Identidade Visual</h1>
        </div>
        <a href="/" target="_blank" rel="noopener noreferrer" data-testid="branding-view-site"
           className="inline-flex items-center gap-2 text-sm text-gray-300 border border-[#2e2e2e] rounded-full px-4 py-2 hover:text-white hover:border-white/30">
          <Eye size={16} /> Visualizar no site
        </a>
      </div>

      {/* Preview + upload */}
      <div className="bm-card p-6 mb-6">
        <h2 className="text-base md:text-lg font-display font-bold text-white uppercase mb-4">Logo principal</h2>
        <div className="grid md:grid-cols-2 gap-6 items-center">
          <div className="rounded-xl border border-[#2e2e2e] bg-[#0d0d0d] p-6 grid place-items-center min-h-[180px]" data-testid="branding-preview">
            <img src={previewSrc} alt="Prévia da logo"
                 className="object-contain" style={{ maxWidth: `min(${width}px, 100%)`, maxHeight: "160px", height: "auto" }} />
          </div>
          <div>
            <p className="text-sm text-gray-400 mb-3">
              {cfg.logo_url ? "Logo personalizada ativa." : "Usando a logo padrão do Brasil Minis (fallback)."}
            </p>
            <input ref={fileRef} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={onUpload} data-testid="branding-file-input" />
            <div className="flex flex-wrap gap-3">
              <button onClick={() => fileRef.current?.click()} disabled={busy} data-testid="branding-upload-btn"
                      className="inline-flex items-center gap-2 bg-[#1E3A8A] text-white font-bold rounded-full px-5 py-2.5 disabled:opacity-60">
                <Upload size={16} /> Enviar nova logo
              </button>
              <button onClick={restore} disabled={busy} data-testid="branding-restore-btn"
                      className="inline-flex items-center gap-2 border border-[#2e2e2e] text-gray-300 font-medium rounded-full px-5 py-2.5 hover:text-white">
                <RotateCcw size={16} /> Restaurar padrão
              </button>
            </div>
            <p className="mt-3 text-xs text-gray-500 flex items-center gap-1"><ImageIcon size={12} /> PNG, JPEG ou WEBP — máx. 3MB.</p>
          </div>
        </div>
      </div>

      {/* Tamanho */}
      <div className="bm-card p-6 mb-6">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-base md:text-lg font-display font-bold text-white uppercase">Tamanho da logo</h2>
          <span className="font-display font-black text-[#FFC107]" data-testid="branding-width-value">{width} px</span>
        </div>
        <input type="range" min={60} max={500} step={5} value={width}
               onChange={(e) => setWidth(parseInt(e.target.value))}
               data-testid="branding-width-slider"
               className="w-full accent-[#FFC107]" />
        <p className="mt-2 text-xs text-gray-500">Largura máxima no desktop (proporção preservada). No mobile reduz automaticamente.</p>
      </div>

      <button onClick={saveWidth} disabled={busy} data-testid="branding-save-btn"
              className="inline-flex items-center gap-2 bg-[#FFC107] text-[#111111] font-bold rounded-full px-6 py-3 disabled:opacity-60">
        <Save size={18} /> Salvar alterações
      </button>
    </div>
  );
}
