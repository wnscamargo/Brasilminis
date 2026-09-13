import { createContext, useContext, useEffect, useState, useCallback } from "react";
import api from "@/lib/api";

const BadgesContext = createContext(null);

export function BadgesProvider({ children }) {
  const [map, setMap] = useState({});
  const refresh = useCallback(async () => {
    try {
      const { data } = await api.get("/badges");
      const m = {};
      (data || []).forEach((b) => { m[b.text] = b; });
      setMap(m);
    } catch { setMap({}); }
  }, []);
  useEffect(() => { refresh(); }, [refresh]);
  return <BadgesContext.Provider value={{ map, refresh }}>{children}</BadgesContext.Provider>;
}

export function useBadges() {
  const ctx = useContext(BadgesContext) || { map: {}, refresh: () => {} };
  const styleFor = (text) => {
    const b = ctx.map[text];
    if (!b) return { backgroundColor: "#FFC107", color: "#111111" };
    return { backgroundColor: b.bg_color || "#FFC107", color: b.text_color || "#111111" };
  };
  return { ...ctx, styleFor };
}
