import { createContext, useContext, useCallback, useEffect, useState } from "react";
import api from "@/lib/api";

const CategoriesContext = createContext(null);

// Fetch ÚNICO da árvore de categorias (principais + subcategorias) já ordenada
// por sort_order/nome no backend. Compartilhado entre Header, Catálogo e menu mobile.
export function CategoriesProvider({ children }) {
  const [tree, setTree] = useState([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/categories?tree=true");
      setTree(Array.isArray(data) ? data : []);
    } catch {
      setTree([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  return (
    <CategoriesContext.Provider value={{ tree, loading, refresh }}>
      {children}
    </CategoriesContext.Provider>
  );
}

export const useCategories = () => useContext(CategoriesContext) || { tree: [], loading: false, refresh: () => {} };

// Helper reutilizável: encontra a "trilha" (principal > subcategoria) de um slug na árvore.
export function findCategoryTrail(tree, slug) {
  if (!slug) return null;
  for (const main of tree) {
    if (main.slug === slug) return { main, sub: null };
    for (const sub of main.children || []) {
      if (sub.slug === slug) return { main, sub };
    }
  }
  return null;
}
