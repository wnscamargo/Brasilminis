import { useEffect, useState } from "react";
import { Plus, Trash2, X } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";

const GROUPS = ["miniaturas", "colecionaveis", "acessorios", "vestuario", "presentes"];

export default function AdminCategories() {
  const [cats, setCats] = useState([]);
  const [show, setShow] = useState(false);
  const [form, setForm] = useState({ name: "", group: "miniaturas", description: "" });

  const load = () => api.get("/categories").then((r) => setCats(r.data));
  useEffect(() => { load(); }, []);

  const save = async (e) => {
    e.preventDefault();
    try {
      await api.post("/admin/categories", form);
      toast.success("Categoria criada");
      setShow(false); setForm({ name: "", group: "miniaturas", description: "" }); load();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };
  const del = async (id) => { if (!window.confirm("Remover?")) return; await api.delete(`/admin/categories/${id}`); load(); };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-display font-black uppercase text-white">Categorias</h1>
        <button onClick={() => setShow(true)} data-testid="new-category-btn" className="bg-[#FFC107] text-[#111111] font-bold rounded-full px-5 py-2.5 flex items-center gap-2"><Plus size={16} /> Nova</button>
      </div>
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {cats.map((c) => (
          <div key={c.id} className="bm-card p-5" data-testid={`admin-category-${c.slug}`}>
            <div className="flex justify-between">
              <span className="text-[#FFC107] text-xs uppercase font-bold">{c.group}</span>
              <button onClick={() => del(c.id)} className="text-gray-500 hover:text-red-400"><Trash2 size={15} /></button>
            </div>
            <p className="text-white font-semibold mt-2">{c.name}</p>
            <p className="text-gray-500 text-xs mt-1 line-clamp-2">{c.description}</p>
          </div>
        ))}
      </div>

      {show && (
        <div className="fixed inset-0 z-[100] bg-black/70 backdrop-blur-sm grid place-items-center p-4">
          <form onSubmit={save} className="bm-card w-full max-w-md p-6">
            <div className="flex justify-between mb-4"><h3 className="text-lg font-display font-bold text-white uppercase">Nova categoria</h3><button type="button" onClick={() => setShow(false)}><X className="text-gray-400" /></button></div>
            <input required placeholder="Nome" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} data-testid="cat-name" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white mb-3" />
            <select value={form.group} onChange={(e) => setForm({ ...form, group: e.target.value })} data-testid="cat-group" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white mb-3">
              {GROUPS.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
            <input placeholder="Descrição" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white mb-4" />
            <button data-testid="save-category-btn" className="w-full bg-[#FFC107] text-[#111111] font-bold rounded-full py-3">Salvar</button>
          </form>
        </div>
      )}
    </div>
  );
}
