import { useEffect, useState } from "react";
import { Plus, Pencil, Trash2, X, Search } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { formatBRL } from "@/lib/brand";

const BADGES = ["NOVO", "LANÇAMENTO", "PROMOÇÃO", "TREASURE HUNT", "SUPER TH", "PREMIUM", "EDIÇÃO LIMITADA", "PRÉ-VENDA", "FRETE GRÁTIS"];
const EMPTY = { name: "", description: "", price: "", compare_at_price: "", category: "", group: "miniaturas", brand: "", images: "", stock: 0, badges: [], featured: false, is_active: true, specs: {} };

export default function AdminProducts() {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState(null);

  const load = () => api.get("/admin/products").then((r) => setProducts(r.data));
  useEffect(() => {
    load();
    api.get("/categories").then((r) => setCategories(r.data));
    api.get("/brands").then((r) => setBrands(r.data));
  }, []);

  const del = async (id) => {
    if (!window.confirm("Remover este produto?")) return;
    await api.delete(`/admin/products/${id}`);
    toast.success("Produto removido");
    load();
  };

  const filtered = products.filter((p) => p.name.toLowerCase().includes(q.toLowerCase()));

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h1 className="text-3xl font-display font-black uppercase text-white">Produtos</h1>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar..." className="bg-[#1f1f1f] border border-[#2e2e2e] rounded-full pl-9 pr-4 py-2.5 text-sm text-white focus:outline-none" />
          </div>
          <button onClick={() => setEditing(EMPTY)} data-testid="new-product-btn" className="bg-[#FFC107] text-[#111111] font-bold rounded-full px-5 py-2.5 flex items-center gap-2">
            <Plus size={16} /> Novo
          </button>
        </div>
      </div>

      <div className="bm-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#111111] text-gray-500 uppercase text-xs">
              <tr>
                <th className="text-left p-4">Produto</th>
                <th className="text-left p-4">Categoria</th>
                <th className="text-left p-4">Preço</th>
                <th className="text-left p-4">Estoque</th>
                <th className="text-right p-4">Ações</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id} className="border-t border-[#2e2e2e]" data-testid={`admin-product-${p.id}`}>
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <img src={p.images?.[0]} alt="" className="h-10 w-10 rounded-lg object-cover" />
                      <span className="text-white line-clamp-1 max-w-[220px]">{p.name}</span>
                    </div>
                  </td>
                  <td className="p-4 text-gray-400">{p.category}</td>
                  <td className="p-4 text-white">{formatBRL(p.price)}</td>
                  <td className="p-4">
                    <span className={p.stock <= 5 ? "text-[#FFC107]" : "text-gray-300"}>{p.stock}</span>
                  </td>
                  <td className="p-4">
                    <div className="flex justify-end gap-2">
                      <button onClick={() => setEditing({ ...p, images: (p.images || []).join(", "), specs: p.specs || {} })} data-testid={`edit-product-${p.id}`} className="p-2 rounded-lg text-gray-400 hover:text-[#FFC107] hover:bg-white/5"><Pencil size={16} /></button>
                      <button onClick={() => del(p.id)} data-testid={`delete-product-${p.id}`} className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-white/5"><Trash2 size={16} /></button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {editing && (
        <ProductModal
          data={editing}
          categories={categories}
          brands={brands}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); load(); }}
        />
      )}
    </div>
  );
}

function ProductModal({ data, categories, brands, onClose, onSaved }) {
  const [form, setForm] = useState(data);
  const [specText, setSpecText] = useState(
    Object.entries(data.specs || {}).map(([k, v]) => `${k}: ${v}`).join("\n")
  );
  const [saving, setSaving] = useState(false);

  const toggleBadge = (b) => {
    setForm((f) => ({ ...f, badges: f.badges.includes(b) ? f.badges.filter((x) => x !== b) : [...f.badges, b] }));
  };

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    const specs = {};
    specText.split("\n").forEach((line) => {
      const [k, ...rest] = line.split(":");
      if (k && rest.length) specs[k.trim()] = rest.join(":").trim();
    });
    const payload = {
      ...form,
      price: parseFloat(form.price),
      compare_at_price: form.compare_at_price ? parseFloat(form.compare_at_price) : null,
      stock: parseInt(form.stock) || 0,
      images: form.images.split(",").map((s) => s.trim()).filter(Boolean),
      specs,
    };
    try {
      if (data.id) await api.put(`/admin/products/${data.id}`, payload);
      else await api.post("/admin/products", payload);
      toast.success("Produto salvo");
      onSaved();
    } catch (err) {
      toast.error(formatApiError(err.response?.data?.detail));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] bg-black/70 backdrop-blur-sm grid place-items-center p-4 overflow-y-auto">
      <form onSubmit={save} className="bm-card w-full max-w-2xl p-6 my-8" data-testid="product-modal">
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-xl font-display font-bold text-white uppercase">{data.id ? "Editar" : "Novo"} produto</h3>
          <button type="button" onClick={onClose}><X className="text-gray-400" /></button>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <TInput label="Nome" value={form.name} onChange={(v) => setForm({ ...form, name: v })} full testid="pf-name" required />
          <TArea label="Descrição" value={form.description} onChange={(v) => setForm({ ...form, description: v })} full testid="pf-desc" />
          <TInput label="Preço" type="number" step="0.01" value={form.price} onChange={(v) => setForm({ ...form, price: v })} testid="pf-price" required />
          <TInput label="Preço comparativo (opcional)" type="number" step="0.01" value={form.compare_at_price || ""} onChange={(v) => setForm({ ...form, compare_at_price: v })} testid="pf-compare" />
          <div>
            <label className="text-xs text-gray-500 block mb-1">Categoria</label>
            <select value={form.category} onChange={(e) => { const c = categories.find((x) => x.slug === e.target.value); setForm({ ...form, category: e.target.value, group: c?.group || form.group }); }} data-testid="pf-category" required className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white">
              <option value="">Selecione</option>
              {categories.map((c) => <option key={c.id} value={c.slug}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Marca</label>
            <select value={form.brand} onChange={(e) => setForm({ ...form, brand: e.target.value })} data-testid="pf-brand" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white">
              <option value="">Sem marca</option>
              {brands.map((b) => <option key={b.id} value={b.slug}>{b.name}</option>)}
            </select>
          </div>
          <TInput label="Estoque" type="number" value={form.stock} onChange={(v) => setForm({ ...form, stock: v })} testid="pf-stock" />
          <TInput label="Imagens (URLs separadas por vírgula)" value={form.images} onChange={(v) => setForm({ ...form, images: v })} full testid="pf-images" />
          <TArea label="Especificações (uma por linha: Chave: Valor)" value={specText} onChange={setSpecText} full testid="pf-specs" />
        </div>

        <div className="mt-4">
          <label className="text-xs text-gray-500 block mb-2">Badges</label>
          <div className="flex flex-wrap gap-2">
            {BADGES.map((b) => (
              <button type="button" key={b} onClick={() => toggleBadge(b)} className={`px-3 py-1 rounded-full text-xs font-semibold border ${form.badges.includes(b) ? "bg-[#1E3A8A] border-[#1E3A8A] text-white" : "border-[#2e2e2e] text-gray-400"}`}>{b}</button>
            ))}
          </div>
        </div>

        <div className="flex gap-4 mt-4">
          <label className="flex items-center gap-2 text-sm text-gray-400"><input type="checkbox" checked={form.featured} onChange={(e) => setForm({ ...form, featured: e.target.checked })} className="accent-[#FFC107]" /> Destaque</label>
          <label className="flex items-center gap-2 text-sm text-gray-400"><input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} className="accent-[#FFC107]" /> Ativo</label>
        </div>

        <div className="flex gap-3 mt-6">
          <button type="button" onClick={onClose} className="flex-1 border border-[#2e2e2e] text-white rounded-full py-3">Cancelar</button>
          <button disabled={saving} data-testid="save-product-btn" className="flex-1 bg-[#FFC107] text-[#111111] font-bold rounded-full py-3">{saving ? "Salvando..." : "Salvar"}</button>
        </div>
      </form>
    </div>
  );
}

function TInput({ label, value, onChange, full, testid, ...rest }) {
  return (
    <div className={full ? "col-span-2" : ""}>
      <label className="text-xs text-gray-500 block mb-1">{label}</label>
      <input value={value} onChange={(e) => onChange(e.target.value)} data-testid={testid} {...rest} className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
    </div>
  );
}
function TArea({ label, value, onChange, full, testid }) {
  return (
    <div className={full ? "col-span-2" : ""}>
      <label className="text-xs text-gray-500 block mb-1">{label}</label>
      <textarea value={value} onChange={(e) => onChange(e.target.value)} data-testid={testid} rows={3} className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-[#1E3A8A]" />
    </div>
  );
}
