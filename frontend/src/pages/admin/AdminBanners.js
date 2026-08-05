import { useEffect, useState } from "react";
import { Plus, Trash2, X, Pencil } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";

const EMPTY = { title: "", subtitle: "", image: "", cta_text: "Comprar Agora", cta_link: "/produtos", position: 0, active: true };

export default function AdminBanners() {
  const [banners, setBanners] = useState([]);
  const [editing, setEditing] = useState(null);

  const load = () => api.get("/admin/banners").then((r) => setBanners(r.data));
  useEffect(() => { load(); }, []);

  const del = async (id) => { if (!window.confirm("Remover?")) return; await api.delete(`/admin/banners/${id}`); load(); };

  const save = async (e) => {
    e.preventDefault();
    try {
      const payload = { ...editing, position: parseInt(editing.position) || 0 };
      if (editing.id) await api.put(`/admin/banners/${editing.id}`, payload);
      else await api.post("/admin/banners", payload);
      toast.success("Banner salvo");
      setEditing(null); load();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-display font-black uppercase text-white">Banners</h1>
        <button onClick={() => setEditing(EMPTY)} data-testid="new-banner-btn" className="bg-[#FFC107] text-[#111111] font-bold rounded-full px-5 py-2.5 flex items-center gap-2"><Plus size={16} /> Novo</button>
      </div>

      <div className="grid md:grid-cols-2 gap-4">
        {banners.map((b) => (
          <div key={b.id} className="bm-card overflow-hidden" data-testid={`admin-banner-${b.id}`}>
            <div className="relative h-40">
              <img src={b.image} alt="" className="h-full w-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 to-transparent" />
              <div className="absolute bottom-3 left-4">
                <p className="text-white font-display font-bold">{b.title}</p>
                <p className="text-gray-300 text-xs">{b.subtitle}</p>
              </div>
              {!b.active && <span className="absolute top-3 right-3 bg-red-500/80 text-white text-xs px-2 py-1 rounded-full">Inativo</span>}
            </div>
            <div className="p-3 flex justify-end gap-2">
              <button onClick={() => setEditing(b)} className="p-2 text-gray-400 hover:text-[#FFC107]"><Pencil size={15} /></button>
              <button onClick={() => del(b.id)} className="p-2 text-gray-400 hover:text-red-400"><Trash2 size={15} /></button>
            </div>
          </div>
        ))}
      </div>

      {editing && (
        <div className="fixed inset-0 z-[100] bg-black/70 backdrop-blur-sm grid place-items-center p-4">
          <form onSubmit={save} className="bm-card w-full max-w-lg p-6">
            <div className="flex justify-between mb-4"><h3 className="text-lg font-display font-bold text-white uppercase">{editing.id ? "Editar" : "Novo"} banner</h3><button type="button" onClick={() => setEditing(null)}><X className="text-gray-400" /></button></div>
            {[["title","Título"],["subtitle","Subtítulo"],["image","URL da imagem"],["cta_text","Texto do botão"],["cta_link","Link do botão"]].map(([k,l]) => (
              <input key={k} required={k==="title"||k==="image"} placeholder={l} value={editing[k]} onChange={(e) => setEditing({ ...editing, [k]: e.target.value })} data-testid={`banner-${k}`} className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white mb-3" />
            ))}
            <label className="flex items-center gap-2 text-sm text-gray-400 mb-4"><input type="checkbox" checked={editing.active} onChange={(e) => setEditing({ ...editing, active: e.target.checked })} className="accent-[#FFC107]" /> Ativo</label>
            <button data-testid="save-banner-btn" className="w-full bg-[#FFC107] text-[#111111] font-bold rounded-full py-3">Salvar</button>
          </form>
        </div>
      )}
    </div>
  );
}
