import { useEffect, useState } from "react";
import api from "@/lib/api";

// Cache simples em módulo: 1 fetch de /site-content compartilhado entre páginas.
let _cache = null;
let _promise = null;

export function useSiteContent() {
  const [data, setData] = useState(_cache);
  const [loading, setLoading] = useState(!_cache);

  useEffect(() => {
    if (_cache) return;
    if (!_promise) {
      _promise = api.get("/site-content").then((r) => {
        _cache = r.data;
        return r.data;
      }).catch(() => ({ pages: {}, social_links: {} }));
    }
    let alive = true;
    _promise.then((d) => {
      if (alive) { setData(d); setLoading(false); }
    });
    return () => { alive = false; };
  }, []);

  return { pages: data?.pages || {}, social: data?.social_links || {}, loading };
}

export function invalidateSiteContent() {
  _cache = null;
  _promise = null;
}
