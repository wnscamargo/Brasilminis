import { useEffect, useState, useCallback } from "react";
import { Plus, Trash2, X, Pencil, ChevronRight, FolderTree, Eye, EyeOff, Boxes, Home, Star } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";
import { formatBRL } from "@/lib/brand";

export default function AdminCategories() {
  const [tree, setTree] = useState([]);
  const [modal, setModal] = useState(null); // {mode:'main'|'sub'|'edit', parent, data}
  const [viewing, setViewing] = useState(null); // categoria/sub para "Ver produtos"

  const load = useCallback(() => api.get("/admin/categories/tree").then((r) => setTree(r.data)), []);
  useEffect(() => { load(); }, [load]);

  const toggleActive = async (cat) => {
    try {
      await api.put(`/admin/categories/${cat.id}`, { name: cat.name, is_active: !cat.is_active });
      toast.success(cat.is_active ? "Categoria desativada" : "Categoria ativada");
      load();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };

  const del = async (cat) => {
    if (!window.confirm(`Remover "${cat.name}"?`)) return;
    try {
      await api.delete(`/admin/categories/${cat.id}`);
      toast.success("Categoria removida");
      load();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
  };

  const roots = tree;

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <h1 className="text-3xl font-display font-black uppercase text-white">Categorias</h1>
        <button onClick={() => setModal({ mode: "main" })} data-testid="new-category-btn" className="bg-[#FFC107] text-[#111111] font-bold rounded-full px-5 py-2.5 flex items-center gap-2">
          <Plus size={16} /> Nova categoria
        </button>
      </div>

      <div className="bm-card p-4 lg:p-6">
        {roots.length === 0 && <p className="text-gray-500 text-sm py-8 text-center">Nenhuma categoria ainda.</p>}
        <div className="space-y-4">
          {roots.map((cat) => (
            <div key={cat.id} data-testid={`admin-category-${cat.slug}`} className="border border-[#2e2e2e] rounded-xl overflow-hidden">
              <div className="flex items-center justify-between gap-3 bg-[#151515] px-4 py-3">
                <div className="flex items-center gap-3 min-w-0">
                  <FolderTree size={18} className="text-[#FFC107] shrink-0" />
                  <div className="min-w-0">
                    <p className={`font-display font-bold uppercase truncate ${cat.is_active ? "text-white" : "text-gray-500 line-through"}`}>{cat.name}</p>
                    <p className="text-xs text-gray-500">{cat.children?.length || 0} subcategoria(s) · {cat.product_count} produto(s)</p>
                  </div>
                </div>
                <div className="flex items-center gap-1 shrink-0">
                  <IconBtn testid={`add-sub-${cat.slug}`} title="Adicionar subcategoria" onClick={() => setModal({ mode: "sub", parent: cat })}><Plus size={16} /></IconBtn>
                  <IconBtn testid={`view-products-${cat.slug}`} title="Ver produtos" onClick={() => setViewing(cat)}><Boxes size={16} /></IconBtn>
                  {cat.show_on_home && <span title="Na Home" className="text-[#009B3A]"><Home size={15} /></span>}
                  {cat.featured && <span title="Destaque" className="text-[#FFC107]"><Star size={14} /></span>}
                  <IconBtn testid={`toggle-${cat.slug}`} title={cat.is_active ? "Desativar" : "Ativar"} onClick={() => toggleActive(cat)}>{cat.is_active ? <Eye size={16} /> : <EyeOff size={16} />}</IconBtn>
                  <IconBtn testid={`edit-${cat.slug}`} title="Editar" onClick={() => setModal({ mode: "edit", data: cat })}><Pencil size={16} /></IconBtn>
                  <IconBtn testid={`del-${cat.slug}`} title="Excluir" danger onClick={() => del(cat)}><Trash2 size={16} /></IconBtn>
                </div>
              </div>
              {(cat.children || []).length > 0 && (
                <div className="divide-y divide-[#222]">
                  {cat.children.map((sub) => (
                    <div key={sub.id} data-testid={`admin-subcategory-${sub.slug}`} className="flex items-center justify-between gap-3 px-4 py-2.5 pl-10">
                      <div className="flex items-center gap-2 min-w-0">
                        <ChevronRight size={14} className="text-gray-600 shrink-0" />
                        <span className={`text-sm truncate ${sub.is_active ? "text-gray-200" : "text-gray-600 line-through"}`}>{sub.name}</span>
                        <span className="text-xs text-gray-600">· {sub.product_count}</span>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <IconBtn testid={`view-products-${sub.slug}`} title="Ver produtos" onClick={() => setViewing(sub)}><Boxes size={15} /></IconBtn>
                        {sub.show_on_home && <span title="Na Home" className="text-[#009B3A]"><Home size={13} /></span>}
                        <IconBtn testid={`toggle-${sub.slug}`} onClick={() => toggleActive(sub)}>{sub.is_active ? <Eye size={15} /> : <EyeOff size={15} />}</IconBtn>
                        <IconBtn testid={`edit-${sub.slug}`} onClick={() => setModal({ mode: "edit", data: sub, roots })}><Pencil size={15} /></IconBtn>
                        <IconBtn testid={`del-${sub.slug}`} danger onClick={() => del(sub)}><Trash2 size={15} /></IconBtn>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {modal && (
        <CategoryModal modal={modal} roots={roots} onClose={() => setModal(null)} onSaved={() => { setModal(null); load(); }} />
      )}
      {viewing && <CategoryProductsModal cat={viewing} onClose={() => setViewing(null)} />}
    </div>
  );
}

function CategoryProductsModal({ cat, onClose }) {
  const [data, setData] = useState({ items: [], total: 0 });
  const [q, setQ] = useState("");
  const [active, setActive] = useState("");
  const [stock, setStock] = useState("");
  const [sort, setSort] = useState("recent");
  const [page, setPage] = useState(1);
  const limit = 10;
  useEffect(() => {
    const p = new URLSearchParams({ category: cat.slug, sort, page, limit });
    if (q) p.set("search", q);
    if (active) p.set("active", active);
    if (stock) p.set("stock", stock);
    api.get(`/admin/catalog/products?${p.toString()}`).then((r) => setData(r.data));
  }, [cat.slug, q, active, stock, sort, page]);
  const pages = Math.max(1, Math.ceil((data.total || 0) / limit));
  const sel = "bg-[#111] border border-[#2e2e2e] rounded-lg px-2 py-2 text-xs text-white";
  return (
    <div className="fixed inset-0 z-[100] bg-black/70 grid place-items-center p-4" data-testid="category-products-modal">
      <div className="bm-card p-5 w-full max-w-3xl max-h-[85vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-display font-black uppercase text-white">Produtos · {cat.name} <span className="text-gray-500 text-sm">({data.total})</span></h3>
          <button onClick={onClose}><X className="text-gray-400" /></button>
        </div>
        <div className="flex flex-wrap gap-2 mb-3">
          <input value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} placeholder="Buscar nome/SKU" data-testid="catprod-search" className={`${sel} flex-1 min-w-[140px]`} />
          <select value={active} onChange={(e) => { setPage(1); setActive(e.target.value); }} data-testid="catprod-active" className={sel}><option value="">Todos</option><option value="true">Ativos</option><option value="false">Inativos</option></select>
          <select value={stock} onChange={(e) => { setPage(1); setStock(e.target.value); }} data-testid="catprod-stock" className={sel}><option value="">Estoque: todos</option><option value="in">Com estoque</option><option value="out">Sem estoque</option></select>
          <select value={sort} onChange={(e) => setSort(e.target.value)} data-testid="catprod-sort" className={sel}><option value="recent">Recentes</option><option value="name">Nome</option><option value="price_asc">Preço ↑</option><option value="price_desc">Preço ↓</option><option value="stock_asc">Estoque ↑</option><option value="stock_desc">Estoque ↓</option></select>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#111] text-gray-500 uppercase text-xs"><tr><th className="text-left p-3">Produto</th><th className="text-left p-3">SKU</th><th className="text-left p-3">Preço</th><th className="text-left p-3">Estoque</th><th className="text-left p-3">Badges</th><th className="text-left p-3">Ativo</th></tr></thead>
            <tbody>
              {data.items.length === 0 && <tr><td colSpan={6} className="p-6 text-center text-gray-500">Nenhum produto neste nó.</td></tr>}
              {data.items.map((p) => (
                <tr key={p.id} className="border-t border-[#2e2e2e]" data-testid={`catprod-row-${p.id}`}>
                  <td className="p-3"><div className="flex items-center gap-2"><img src={p.images?.[0]} alt="" className="h-9 w-9 rounded object-cover bg-[#222]" /><span className="text-white line-clamp-1 max-w-[200px]">{p.name}</span></div></td>
                  <td className="p-3 text-gray-400">{p.sku || "—"}</td>
                  <td className="p-3 text-white">{formatBRL(p.price)}</td>
                  <td className="p-3 text-gray-300">{p.stock}</td>
                  <td className="p-3 text-gray-400 text-xs">{(p.badges || []).join(", ") || "—"}</td>
                  <td className="p-3">{p.is_active ? <span className="text-[#009B3A]">Sim</span> : <span className="text-gray-600">Não</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {pages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-4">
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} className="px-3 py-1.5 text-xs border border-[#2e2e2e] rounded-full text-gray-300 disabled:opacity-40">Anterior</button>
            <span className="text-xs text-gray-400">{page} / {pages}</span>
            <button disabled={page >= pages} onClick={() => setPage((p) => p + 1)} className="px-3 py-1.5 text-xs border border-[#2e2e2e] rounded-full text-gray-300 disabled:opacity-40">Próxima</button>
          </div>
        )}
      </div>
    </div>
  );
}

function IconBtn({ children, onClick, danger, title, testid }) {
  return (
    <button onClick={onClick} title={title} data-testid={testid} className={`p-2 rounded-lg text-gray-400 hover:bg-white/5 ${danger ? "hover:text-red-400" : "hover:text-[#FFC107]"}`}>{children}</button>
  );
}

function CategoryModal({ modal, roots, onClose, onSaved }) {
  const isEdit = modal.mode === "edit";
  const [name, setName] = useState(modal.data?.name || "");
  const [description, setDescription] = useState(modal.data?.description || "");
  const [image, setImage] = useState(modal.data?.image || "");
  const [icon, setIcon] = useState(modal.data?.icon || "");
  const [showOnHome, setShowOnHome] = useState(!!modal.data?.show_on_home);
  const [featured, setFeatured] = useState(!!modal.data?.featured);
  const [parentId, setParentId] = useState(
    modal.mode === "sub" ? modal.parent?.id : (modal.data?.parent_id || "")
  );
  const [saving, setSaving] = useState(false);

  const title = modal.mode === "main" ? "Nova categoria principal" : modal.mode === "sub" ? `Nova subcategoria em "${modal.parent?.name}"` : "Editar categoria";
  const isSubEdit = isEdit && modal.data?.parent_id;

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    const payload = { name, description, image, icon, show_on_home: showOnHome, featured };
    if (modal.mode === "sub") payload.parent_id = modal.parent.id;
    if (isSubEdit) payload.parent_id = parentId || null; // permite mover subcategoria
    try {
      if (isEdit) await api.put(`/admin/categories/${modal.data.id}`, payload);
      else await api.post("/admin/categories", payload);
      toast.success("Categoria salva");
      onSaved();
    } catch (err) { toast.error(formatApiError(err.response?.data?.detail)); }
    finally { setSaving(false); }
  };

  return (
    <div className="fixed inset-0 z-[100] bg-black/70 backdrop-blur-sm grid place-items-center p-4">
      <form onSubmit={save} className="bm-card w-full max-w-md p-6" data-testid="category-modal">
        <div className="flex justify-between mb-4"><h3 className="text-lg font-display font-bold text-white uppercase">{title}</h3><button type="button" onClick={onClose}><X className="text-gray-400" /></button></div>
        <label className="text-xs text-gray-500 block mb-1">Nome</label>
        <input required placeholder="Nome" value={name} onChange={(e) => setName(e.target.value)} data-testid="cat-name" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white mb-3" />
        {isSubEdit && (
          <>
            <label className="text-xs text-gray-500 block mb-1">Categoria principal (mover)</label>
            <select value={parentId} onChange={(e) => setParentId(e.target.value)} data-testid="cat-move-parent" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white mb-3">
              {roots.map((r) => <option key={r.id} value={r.id}>{r.name}</option>)}
            </select>
          </>
        )}
        <label className="text-xs text-gray-500 block mb-1">Descrição</label>
        <input placeholder="Descrição" value={description} onChange={(e) => setDescription(e.target.value)} className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white mb-3" />
        <label className="text-xs text-gray-500 block mb-1">Imagem/capa (URL)</label>
        <input placeholder="https://..." value={image} onChange={(e) => setImage(e.target.value)} data-testid="cat-image" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white mb-3" />
        <label className="text-xs text-gray-500 block mb-1">Ícone (opcional)</label>
        <input placeholder="ex: Sparkles ou emoji" value={icon} onChange={(e) => setIcon(e.target.value)} data-testid="cat-icon" className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white mb-4" />
        <div className="flex flex-wrap gap-4 mb-4">
          <label className="flex items-center gap-2 text-sm text-gray-300"><input type="checkbox" checked={showOnHome} onChange={(e) => setShowOnHome(e.target.checked)} data-testid="cat-show-on-home" className="accent-[#FFC107]" /> Exibir na Home</label>
          <label className="flex items-center gap-2 text-sm text-gray-300"><input type="checkbox" checked={featured} onChange={(e) => setFeatured(e.target.checked)} data-testid="cat-featured" className="accent-[#FFC107]" /> Destaque</label>
        </div>
        <button disabled={saving} data-testid="save-category-btn" className="w-full bg-[#FFC107] text-[#111111] font-bold rounded-full py-3">{saving ? "Salvando..." : "Salvar"}</button>
      </form>
    </div>
  );
}
