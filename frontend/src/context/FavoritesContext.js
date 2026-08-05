import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import api from "@/lib/api";
import { useAuth } from "@/context/AuthContext";

const FavContext = createContext(null);

export function FavoritesProvider({ children }) {
  const { user } = useAuth();
  const [ids, setIds] = useState([]);
  const [products, setProducts] = useState([]);

  const load = useCallback(async () => {
    if (!user) {
      setIds([]);
      setProducts([]);
      return;
    }
    try {
      const { data } = await api.get("/favorites");
      setProducts(data);
      setIds(data.map((p) => p.id));
    } catch {}
  }, [user]);

  useEffect(() => {
    load();
  }, [load]);

  const toggle = async (product) => {
    if (!user) {
      toast.error("Entre para salvar seus favoritos");
      return false;
    }
    if (ids.includes(product.id)) {
      setIds((p) => p.filter((i) => i !== product.id));
      setProducts((p) => p.filter((i) => i.id !== product.id));
      await api.delete(`/favorites/${product.id}`);
      toast("Removido dos favoritos");
    } else {
      setIds((p) => [...p, product.id]);
      setProducts((p) => [...p, product]);
      await api.post(`/favorites/${product.id}`);
      toast.success("Adicionado aos favoritos");
    }
    return true;
  };

  return (
    <FavContext.Provider value={{ ids, products, toggle, reload: load }}>
      {children}
    </FavContext.Provider>
  );
}

export const useFavorites = () => useContext(FavContext);
