import { useEffect, useState, useCallback, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { Plus, Pencil, Trash2, X, Search, Star, Upload, Link as LinkIcon, ArrowUp, ArrowDown, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { formatBRL } from "@/lib/brand";

const EMPTY = { name: "", description: "", price: "", compare_at_price: "", cost_price: "", main_category_id: "", subcategory_id: "", brand: "", images: "", stock: 0, weight_kg: "", width_cm: "", height_cm: "", length_cm: "", sku: "", barcode: "", badges: [], featured: false, is_active: true, specs: {} };

function margin(price, cost) {
  const p = parseFloat(price), c = parseFloat(cost);
  if (!p || isNaN(c) || cost === "" || cost === null || cost === undefined) return null;
  const profit = p - c;
  return { profit, pct: p > 0 ? (profit / p) * 100 : 0 };
}

export default function AdminProducts() {
  const [products, setProducts] = useState([]);
  const [tree, setTree] = useState([]);
  const [brands, setBrands] = useState([]);
  const [badgeOptions, setBadgeOptions] = useState([]);
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const load = useCallback(() => api.get("/admin/products").then((r) => setProducts(r.data)), []);
  useEffect(() => {
    load();
    api.get("/admin/categories/tree").then((r) => setTree(r.data));
    api.get("/brands").then((r) => setBrands(r.data));
    api.get("/admin/badges").then((r) => setBadgeOptions(r.data.filter((b) => b.active)));
  }, [load]);

  // Abre o editor diretamente quando vier de "Ver produtos" (/admin/produtos?edit=<id>)
  useEffect(() => {
    const editId = searchParams.get("edit");
    if (editId && products.length) {
      const p = products.find((x) => x.id === editId);
      if (p) { setEditing(p); searchParams.delete("edit"); setSearchParams(searchParams, { replace: true }); }
    }
  }, [searchParams, products, setSearchParams]);

  const del = async (id) => {
    if (!window.confirm("Remover este produto?")) return;
    await api.delete(`/admin/products/${id}`);
    toast.success("Produto removido");
    load();
  };

  const filtered = products.filter((p) => p.name.toLowerCase().includes(q.toLowerCase()));
  const bmap = {};
  badgeOptions.forEach((b) => { bmap[b.text] = b; });
  const badgeStyle = (t) => (bmap[t] ? { backgroundColor: bmap[t].bg_color, color: bmap[t].text_color } : { backgroundColor: "#2e2e2e", color: "#e5e7eb" });

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
                <th className="text-left p-4">Preço</th>
                <th className="text-left p-4">Custo</th>
                <th className="text-left p-4">Margem</th>
                <th className="text-left p-4">Estoque</th>
                <th className="text-left p-4">Badges</th>
                <th className="text-right p-4">Ações</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => {
                const m = margin(p.price, p.cost_price);
                return (
                  <tr key={p.id} className="border-t border-[#2e2e2e]" data-testid={`admin-product-${p.id}`}>
                    <td className="p-4">
                      <div className="flex items-center gap-3">
                        <img src={p.images?.[0]} alt="" className="h-10 w-10 rounded-lg object-cover bg-[#222]" />
                        <span className="text-white line-clamp-1 max-w-[220px]">{p.name}</span>
                      </div>
                    </td>
                    <td className="p-4 text-white">{formatBRL(p.price)}</td>
                    <td className="p-4">{p.cost_price == null ? <span className="text-[#FFC107] text-xs">sem custo</span> : <span className="text-gray-300">{formatBRL(p.cost_price)}</span>}</td>
                    <td className="p-4" data-testid={`margin-${p.id}`}>{m ? <span className={m.pct < 20 ? "text-red-400" : "text-[#009B3A]"}>{m.pct.toFixed(1)}%</span> : <span className="text-gray-600">—</span>}</td>
                    <td className="p-4"><span className={p.stock <= 5 ? "text-[#FFC107]" : "text-gray-300"}>{p.stock}</span></td>
                    <td className="p-4" data-testid={`product-badges-${p.id}`}>
                      {(p.badges && p.badges.length) ? (
                        <div className="flex flex-wrap gap-1 max-w-[220px]">
                          {p.badges.map((t) => (
                            <span key={t} style={badgeStyle(t)} className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide rounded-full whitespace-nowrap">{t}</span>
                          ))}
                        </div>
                      ) : <span className="text-gray-600">—</span>}
                    </td>
                    <td className="p-4">
                      <div className="flex justify-end gap-2">
                        <button onClick={() => setEditing({ ...p, cost_price: p.cost_price ?? "", compare_at_price: p.compare_at_price ?? "", main_category_id: p.main_category_id || "", subcategory_id: p.subcategory_id || "", weight_kg: p.weight_kg ?? "", width_cm: p.width_cm ?? "", height_cm: p.height_cm ?? "", length_cm: p.length_cm ?? "", sku: p.sku ?? "", barcode: p.barcode ?? "", images: "", specs: p.specs || {} })} data-testid={`edit-product-${p.id}`} className="p-2 rounded-lg text-gray-400 hover:text-[#FFC107] hover:bg-white/5"><Pencil size={16} /></button>
                        <button onClick={() => del(p.id)} data-testid={`delete-product-${p.id}`} className="p-2 rounded-lg text-gray-400 hover:text-red-400 hover:bg-white/5"><Trash2 size={16} /></button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {editing && (
        <ProductModal data={editing} tree={tree} brands={brands} badgeOptions={badgeOptions} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />
      )}
    </div>
  );
}

function ProductModal({ data, tree, brands, badgeOptions = [], onClose, onSaved }) {
  const [form, setForm] = useState(data);
  const [specText, setSpecText] = useState(Object.entries(data.specs || {}).map(([k, v]) => `${k}: ${v}`).join("\n"));
  const [saving, setSaving] = useState(false);

  const mainCat = tree.find((c) => c.id === form.main_category_id);
  const subs = mainCat?.children || [];
  const m = margin(form.price, form.cost_price);
  const shipIncomplete = ![form.weight_kg, form.width_cm, form.height_cm, form.length_cm].every((v) => v !== "" && v != null && parseFloat(v) > 0);

  const toggleBadge = (b) => setForm((f) => ({ ...f, badges: f.badges.includes(b) ? f.badges.filter((x) => x !== b) : [...f.badges, b] }));

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    const specs = {};
    specText.split("\n").forEach((line) => { const [k, ...rest] = line.split(":"); if (k && rest.length) specs[k.trim()] = rest.join(":").trim(); });
    const payload = {
      name: form.name, description: form.description,
      price: parseFloat(form.price),
      compare_at_price: form.compare_at_price !== "" && form.compare_at_price != null ? parseFloat(form.compare_at_price) : null,
      cost_price: form.cost_price !== "" && form.cost_price != null ? parseFloat(form.cost_price) : null,
      main_category_id: form.main_category_id || null,
      subcategory_id: form.subcategory_id || null,
      brand: form.brand || "",
      stock: parseInt(form.stock) || 0,
      weight_kg: form.weight_kg !== "" && form.weight_kg != null ? parseFloat(form.weight_kg) : null,
      width_cm: form.width_cm !== "" && form.width_cm != null ? parseFloat(form.width_cm) : null,
      height_cm: form.height_cm !== "" && form.height_cm != null ? parseFloat(form.height_cm) : null,
      length_cm: form.length_cm !== "" && form.length_cm != null ? parseFloat(form.length_cm) : null,
      sku: form.sku || null,
      barcode: form.barcode || null,
      badges: form.badges, specs, featured: form.featured, is_active: form.is_active,
      images: data.id ? [] : String(form.images || "").split(",").map((s) => s.trim()).filter(Boolean),
    };
    try {
      if (data.id) await api.put(`/admin/products/${data.id}`, payload);
      else await api.post("/admin/products", payload);
      toast.success("Produto salvo");
      onSaved();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
    finally { setSaving(false); }
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
          <TInput label="Preço de venda" type="number" step="0.01" value={form.price} onChange={(v) => setForm({ ...form, price: v })} testid="pf-price" required />
          <TInput label="Preço comparativo (opcional)" type="number" step="0.01" value={form.compare_at_price} onChange={(v) => setForm({ ...form, compare_at_price: v })} testid="pf-compare" />
          <TInput label="Custo do produto" type="number" step="0.01" min="0" value={form.cost_price} onChange={(v) => setForm({ ...form, cost_price: v })} testid="pf-cost" />
          <div className="flex flex-col justify-end">
            <label className="text-xs text-gray-500 block mb-1">Lucro / Margem</label>
            <div data-testid="pf-margin" className="bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm">
              {m ? <span className="text-[#009B3A] font-semibold">{formatBRL(m.profit)} · {m.pct.toFixed(2)}%</span> : <span className="text-gray-600">informe custo e preço</span>}
            </div>
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Categoria principal</label>
            <select value={form.main_category_id} onChange={(e) => setForm({ ...form, main_category_id: e.target.value, subcategory_id: "" })} data-testid="pf-main-category" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white">
              <option value="">Selecione</option>
              {tree.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-gray-500 block mb-1">Subcategoria</label>
            <select value={form.subcategory_id} onChange={(e) => setForm({ ...form, subcategory_id: e.target.value })} data-testid="pf-subcategory" disabled={!form.main_category_id} className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white disabled:opacity-50">
              <option value="">{form.main_category_id ? "Sem subcategoria" : "Escolha a categoria"}</option>
              {subs.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
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
          {!data.id && <TInput label="Imagens iniciais (URLs por vírgula)" value={form.images} onChange={(v) => setForm({ ...form, images: v })} full testid="pf-images" />}
          <TArea label="Especificações (uma por linha: Chave: Valor)" value={specText} onChange={setSpecText} full testid="pf-specs" />
        </div>

        <div className="mt-5 border-t border-[#2e2e2e] pt-5">
          <div className="flex items-center justify-between mb-3">
            <label className="text-xs text-gray-500 uppercase font-bold tracking-wide">Dados logísticos (frete)</label>
            {shipIncomplete && <span data-testid="ship-incomplete-alert" className="text-xs text-[#FFC107] flex items-center gap-1"><AlertTriangle size={13} /> Dados de frete incompletos</span>}
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <TInput label="Peso (kg)" type="number" step="0.001" value={form.weight_kg} onChange={(v) => setForm({ ...form, weight_kg: v })} testid="pf-weight" />
            <TInput label="Largura (cm)" type="number" step="0.1" value={form.width_cm} onChange={(v) => setForm({ ...form, width_cm: v })} testid="pf-width" />
            <TInput label="Altura (cm)" type="number" step="0.1" value={form.height_cm} onChange={(v) => setForm({ ...form, height_cm: v })} testid="pf-height" />
            <TInput label="Comprimento (cm)" type="number" step="0.1" value={form.length_cm} onChange={(v) => setForm({ ...form, length_cm: v })} testid="pf-length" />
            <TInput label="SKU (opcional)" value={form.sku} onChange={(v) => setForm({ ...form, sku: v })} testid="pf-sku" />
            <TInput label="Código de barras (opcional)" value={form.barcode} onChange={(v) => setForm({ ...form, barcode: v })} testid="pf-barcode" />
          </div>
        </div>

        <div className="mt-4">
          <label className="text-xs text-gray-500 block mb-2">Badges</label>
          <div className="flex flex-wrap gap-2">
            {badgeOptions.length === 0 && <span className="text-xs text-gray-600">Nenhum badge cadastrado. Crie em Catálogo → Badges.</span>}
            {badgeOptions.map((bo) => (
              <button type="button" key={bo.id} onClick={() => toggleBadge(bo.text)} data-testid={`pf-badge-${bo.text}`}
                style={form.badges.includes(bo.text) ? { backgroundColor: bo.bg_color, color: bo.text_color, borderColor: bo.bg_color } : {}}
                className={`px-3 py-1 rounded-full text-xs font-semibold border ${form.badges.includes(bo.text) ? "" : "border-[#2e2e2e] text-gray-400"}`}>{bo.text}</button>
            ))}
          </div>
        </div>

        <div className="flex gap-4 mt-4">
          <label className="flex items-center gap-2 text-sm text-gray-400"><input type="checkbox" checked={form.featured} onChange={(e) => setForm({ ...form, featured: e.target.checked })} className="accent-[#FFC107]" /> Destaque</label>
          <label className="flex items-center gap-2 text-sm text-gray-400"><input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} className="accent-[#FFC107]" /> Ativo</label>
        </div>

        {data.id && <ProductImages productId={data.id} />}

        <div className="flex gap-3 mt-6">
          <button type="button" onClick={onClose} className="flex-1 border border-[#2e2e2e] text-white rounded-full py-3">Fechar</button>
          <button disabled={saving} data-testid="save-product-btn" className="flex-1 bg-[#FFC107] text-[#111111] font-bold rounded-full py-3">{saving ? "Salvando..." : "Salvar"}</button>
        </div>
      </form>
    </div>
  );
}

function ProductImages({ productId }) {
  const [images, setImages] = useState([]);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const fileRef = useRef();

  const load = useCallback(() => api.get(`/admin/products/${productId}/images`).then((r) => setImages(r.data)), [productId]);
  useEffect(() => { load(); }, [load]);

  const addUrl = async () => {
    if (!url.trim()) return;
    setBusy(true);
    try { await api.post(`/admin/products/${productId}/images`, { url: url.trim() }); setUrl(""); toast.success("Imagem adicionada"); load(); }
    catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
    finally { setBusy(false); }
  };

  const upload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBusy(true);
    const fd = new FormData();
    fd.append("file", file);
    try { await api.post(`/admin/products/${productId}/images/upload`, fd, { headers: { "Content-Type": "multipart/form-data" } }); toast.success("Upload concluído"); load(); }
    catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
    finally { setBusy(false); if (fileRef.current) fileRef.current.value = ""; }
  };

  const setPrimary = async (id) => { await api.put(`/admin/products/${productId}/images/${id}/primary`); load(); };
  const remove = async (id) => { await api.delete(`/admin/products/${productId}/images/${id}`); toast.success("Imagem removida"); load(); };
  const move = async (index, dir) => {
    const next = [...images];
    const j = index + dir;
    if (j < 0 || j >= next.length) return;
    [next[index], next[j]] = [next[j], next[index]];
    setImages(next);
    await api.put(`/admin/products/${productId}/images/reorder`, { ids: next.map((i) => i.id) });
    load();
  };

  return (
    <div className="mt-6 border-t border-[#2e2e2e] pt-5" data-testid="product-images-section">
      <label className="text-xs text-gray-500 block mb-3 uppercase font-bold tracking-wide">Imagens do produto</label>
      <div className="flex flex-wrap gap-3 mb-4">
        {images.length === 0 && <p className="text-gray-600 text-sm">Nenhuma imagem ainda.</p>}
        {images.map((img, i) => (
          <div key={img.id} data-testid={`prod-img-${img.id}`} className={`relative group w-24 h-24 rounded-lg overflow-hidden border ${img.is_primary ? "border-[#FFC107]" : "border-[#2e2e2e]"}`}>
            <img src={img.url} alt="" className="w-full h-full object-cover bg-[#222]" />
            {img.is_primary && <span className="absolute top-1 left-1 bg-[#FFC107] text-[#111] text-[9px] font-bold px-1.5 py-0.5 rounded">PRINCIPAL</span>}
            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-1">
              <div className="flex gap-1">
                <button type="button" title="Mover" onClick={() => move(i, -1)} className="p-1 text-white hover:text-[#FFC107]"><ArrowUp size={14} /></button>
                <button type="button" title="Mover" onClick={() => move(i, 1)} className="p-1 text-white hover:text-[#FFC107]"><ArrowDown size={14} /></button>
              </div>
              <div className="flex gap-1">
                {!img.is_primary && <button type="button" title="Tornar principal" data-testid={`set-primary-${img.id}`} onClick={() => setPrimary(img.id)} className="p-1 text-white hover:text-[#FFC107]"><Star size={14} /></button>}
                <button type="button" title="Excluir" data-testid={`del-img-${img.id}`} onClick={() => remove(img.id)} className="p-1 text-white hover:text-red-400"><Trash2 size={14} /></button>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="flex flex-col sm:flex-row gap-2">
        <div className="flex-1 flex gap-2">
          <div className="relative flex-1">
            <LinkIcon size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
            <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://..." data-testid="img-url-input" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg pl-8 pr-3 py-2.5 text-sm text-white" />
          </div>
          <button type="button" disabled={busy} onClick={addUrl} data-testid="add-img-url-btn" className="bg-[#1E3A8A] text-white rounded-lg px-4 text-sm font-semibold whitespace-nowrap">Adicionar URL</button>
        </div>
        <label className="bg-[#2e2e2e] text-white rounded-lg px-4 py-2.5 text-sm font-semibold flex items-center gap-2 cursor-pointer justify-center" data-testid="upload-img-label">
          <Upload size={14} /> {busy ? "Enviando..." : "Enviar arquivo"}
          <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" onChange={upload} className="hidden" data-testid="upload-img-input" />
        </label>
      </div>
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
