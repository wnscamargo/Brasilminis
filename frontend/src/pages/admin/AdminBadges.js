import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, X } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";

const EMPTY = { text: "", bg_color: "#FFC107", text_color: "#111111", icon: "", priority: 0, sort_order: 0, active: true };

export default function AdminBadges() {
  const [badges, setBadges] = useState([]);
  const [editing, setEditing] = useState(null);
  const load = () => api.get("/admin/badges").then((r) => setBadges(r.data));
  useEffect(() => { load(); }, []);

  const del = async (b) => {
    if (!window.confirm(`Excluir badge "${b.text}"?`)) return;
    try { await api.delete(`/admin/badges/${b.id}`); toast.success("Badge removido"); load(); }
    catch (e) { toast.error(formatApiError(e.response?.data?.detail)); }
  };

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h1 className="text-3xl font-display font-black uppercase text-white">Badges</h1>
        <button onClick={() => setEditing(EMPTY)} data-testid="new-badge-btn" className="bg-[#FFC107] text-[#111] font-bold rounded-full px-5 py-2.5 flex items-center gap-2"><Plus size={16} /> Novo badge</button>
      </div>
      <div className="bm-card overflow-hidden overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-[#111] text-gray-500 uppercase text-xs">
            <tr><th className="text-left p-4">Preview</th><th className="text-left p-4">Texto</th><th className="text-left p-4">Prioridade</th><th className="text-left p-4">Ordem</th><th className="text-left p-4">Status</th><th className="p-4"></th></tr>
          </thead>
          <tbody>
            {badges.length === 0 && <tr><td colSpan={6} className="p-8 text-center text-gray-500">Nenhum badge cadastrado.</td></tr>}
            {badges.map((b) => (
              <tr key={b.id} className="border-t border-[#2e2e2e]" data-testid={`admin-badge-${b.id}`}>
                <td className="p-4"><span className="px-2.5 py-1 text-[11px] font-bold uppercase tracking-wider rounded-full" style={{ backgroundColor: b.bg_color, color: b.text_color }}>{b.text}</span></td>
                <td className="p-4 text-white">{b.text}</td>
                <td className="p-4 text-gray-400">{b.priority}</td>
                <td className="p-4 text-gray-400">{b.sort_order}</td>
                <td className="p-4">{b.active ? <span className="text-[#009B3A]">Ativo</span> : <span className="text-gray-600">Inativo</span>}</td>
                <td className="p-4 text-right whitespace-nowrap">
                  <button onClick={() => setEditing(b)} data-testid={`edit-badge-${b.id}`} className="p-2 text-[#FFC107]"><Pencil size={15} /></button>
                  <button onClick={() => del(b)} data-testid={`del-badge-${b.id}`} className="p-2 text-red-400"><Trash2 size={15} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {editing && <BadgeModal data={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
    </div>
  );
}

function BadgeModal({ data, onClose, onSaved }) {
  const [f, setF] = useState(data);
  const [busy, setBusy] = useState(false);
  const inp = "w-full bg-[#111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white";
  const save = async (e) => {
    e.preventDefault(); setBusy(true);
    const payload = { ...f, priority: parseInt(f.priority) || 0, sort_order: parseInt(f.sort_order) || 0 };
    try {
      if (data.id) await api.put(`/admin/badges/${data.id}`, payload);
      else await api.post("/admin/badges", payload);
      toast.success("Badge salvo"); onSaved();
    } catch (e) { toast.error(formatApiError(e.response?.data?.detail)); setBusy(false); }
  };
  return (
    <div className="fixed inset-0 z-[100] bg-black/70 grid place-items-center p-4" data-testid="badge-modal">
      <form onSubmit={save} className="bm-card p-6 max-w-md w-full">
        <div className="flex items-center justify-between mb-4"><h3 className="text-lg font-display font-black uppercase text-white">{data.id ? "Editar" : "Novo"} badge</h3><button type="button" onClick={onClose}><X className="text-gray-400" /></button></div>
        <div className="mb-4 flex items-center gap-3">
          <span className="text-xs text-gray-500">Preview:</span>
          <span data-testid="badge-preview" className="px-3 py-1 text-[11px] font-bold uppercase tracking-wider rounded-full" style={{ backgroundColor: f.bg_color, color: f.text_color }}>{f.text || "TEXTO"}</span>
        </div>
        <label className="text-xs text-gray-500 block mb-1">Texto</label>
        <input required value={f.text} onChange={(e) => setF({ ...f, text: e.target.value })} data-testid="badge-text" className={`${inp} mb-3`} />
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div><label className="text-xs text-gray-500 block mb-1">Cor de fundo</label><input type="color" value={f.bg_color} onChange={(e) => setF({ ...f, bg_color: e.target.value })} data-testid="badge-bg" className="w-full h-10 bg-[#111] border border-[#2e2e2e] rounded-lg" /></div>
          <div><label className="text-xs text-gray-500 block mb-1">Cor do texto</label><input type="color" value={f.text_color} onChange={(e) => setF({ ...f, text_color: e.target.value })} data-testid="badge-fg" className="w-full h-10 bg-[#111] border border-[#2e2e2e] rounded-lg" /></div>
        </div>
        <div className="grid grid-cols-2 gap-3 mb-3">
          <div><label className="text-xs text-gray-500 block mb-1">Prioridade</label><input type="number" value={f.priority} onChange={(e) => setF({ ...f, priority: e.target.value })} data-testid="badge-priority" className={inp} /></div>
          <div><label className="text-xs text-gray-500 block mb-1">Ordem</label><input type="number" value={f.sort_order} onChange={(e) => setF({ ...f, sort_order: e.target.value })} data-testid="badge-sort" className={inp} /></div>
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-400 mb-4"><input type="checkbox" checked={f.active} onChange={(e) => setF({ ...f, active: e.target.checked })} data-testid="badge-active" className="accent-[#FFC107]" /> Ativo</label>
        <button disabled={busy} data-testid="save-badge-btn" className="w-full bg-[#FFC107] text-[#111] font-bold rounded-full py-3">{busy ? "Salvando..." : "Salvar"}</button>
      </form>
    </div>
  );
}
