import { useEffect, useState } from "react";
import { Plus, Trash2, X } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";

export default function AdminBrands() {
  const [brands, setBrands] = useState([]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ name: "", description: "" });

  const load = () => api.get("/brands").then((r) => setBrands(r.data));
  useEffect(() => { load(); }, []);

  const save = async (e) => {
    e.preventDefault();
    try {
      await api.post("/admin/brands", form);
      toast.success("Marca criada");
      setShow(false); setForm({ name: "", description: "" }); load();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const del = async (id) => { if (!window.confirm("Remover?")) return; await api.delete(`/admin/brands/${id}`); load(); };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-display font-black uppercase text-white">Marcas</h1>
        <button onClick={() => setShow(true)} data-testid="new-brand-btn" className="bg-[#FFC107] text-[#111111] font-bold rounded-full px-5 py-2.5 flex items-center gap-2"><Plus size={16} /> Nova</button>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {brands.map((b) => (
          <div key={b.id} className="bm-card p-5 flex items-center justify-between" data-testid={`admin-brand-${b.slug}`}>
            <span className="text-white font-display font-semibold uppercase">{b.name}</span>
            <button onClick={() => del(b.id)} className="text-gray-500 hover:text-red-400"><Trash2 size={15} /></button>
          </div>
        ))}
      </div>
      {show && (
        <div className="fixed inset-0 z-[100] bg-black/70 backdrop-blur-sm grid place-items-center p-4">
          <form onSubmit={save} className="bm-card w-full max-w-md p-6">
            <div className="flex justify-between mb-4"><h3 className="text-lg font-display font-bold text-white uppercase">Nova marca</h3><button type="button" onClick={() => setShow(false)}><X className="text-gray-400" /></button></div>
            <input required placeholder="Nome" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="brand-name" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white mb-3" />
            <input placeholder="Descrição" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white mb-4" />
            <button data-testid="save-brand-btn" className="w-full bg-[#FFC107] text-[#111111] font-bold rounded-full py-3">Salvar</button>
          </form>
        </div>
      )}
    </div>
  );
}
