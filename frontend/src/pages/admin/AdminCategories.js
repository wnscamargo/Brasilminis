import { useEffect, useState, useCallback } from "react";
import { Plus, Trash2, X, Pencil, ChevronRight, FolderTree, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import api, { formatApiError } from "@/lib/api";

export default function AdminCategories() {
  const [tree, setTree] = useState([]);
  const [modal, setModal] = useState(null); // {mode:'main'|'sub'|'edit', parent, data}

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
  const [parentId, setParentId] = useState(
    modal.mode === "sub" ? modal.parent?.id : (modal.data?.parent_id || "")
  );
  const [saving, setSaving] = useState(false);

  const title = modal.mode === "main" ? "Nova categoria principal" : modal.mode === "sub" ? `Nova subcategoria em "${modal.parent?.name}"` : "Editar categoria";
  const isSubEdit = isEdit && modal.data?.parent_id;

  const save = async (e) => {
    e.preventDefault();
    setSaving(true);
    const payload = { name, description };
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
        <input placeholder="Descrição" value={description} onChange={(e) => setDescription(e.target.value)} className="w-full bg-[#111111] border border-[#2e2e2e] rounded-lg px-3 py-2.5 text-sm text-white mb-4" />
        <button disabled={saving} data-testid="save-category-btn" className="w-full bg-[#FFC107] text-[#111111] font-bold rounded-full py-3">{saving ? "Salvando..." : "Salvar"}</button>
      </form>
    </div>
  );
}
