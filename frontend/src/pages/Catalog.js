import { useEffect, useState, useCallback } from "react";
import { useSearchParams, useParams } from "react-router-dom";
import { SlidersHorizontal, X } from "lucide-react";
import api from "@/lib/api";
import { GROUP_LABELS } from "@/lib/brand";
import ProductCard from "@/components/ProductCard";

const SORTS = [
  { v: "recent", l: "Mais recentes" },
  { v: "price_asc", l: "Menor preço" },
  { v: "price_desc", l: "Maior preço" },
  { v: "rating", l: "Melhor avaliados" },
  { v: "name", l: "Nome (A-Z)" },
];

export default function Catalog() {
  const { group } = useParams();
  const [params, setParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
  const [categories, setCategories] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showFilters, setShowFilters] = useState(false);

  const category = params.get("category") || "";
  const brand = params.get("brand") || "";
  const badge = params.get("badge") || "";
  const search = params.get("search") || "";
  const onSale = params.get("on_sale") || "";
  const sort = params.get("sort") || "recent";

  useEffect(() => {
    api.get("/brands").then((r) => setBrands(r.data));
  }, []);

  useEffect(() => {
    api.get(`/categories${group ? `?group=${group}` : ""}`).then((r) => setCategories(r.data));
  }, [group]);

  const load = useCallback(async () => {
    setLoading(true);
    const qp = new URLSearchParams();
    if (group) qp.set("group", group);
    if (category) qp.set("category", category);
    if (brand) qp.set("brand", brand);
    if (badge) qp.set("badge", badge);
    if (search) qp.set("search", search);
    if (onSale) qp.set("on_sale", "true");
    qp.set("sort", sort);
    qp.set("limit", "48");
    try {
      const { data } = await api.get(`/products?${qp.toString()}`);
      setProducts(data.items);
      setTotal(data.total);
    } finally {
      setLoading(false);
    }
  }, [group, category, brand, badge, search, onSale, sort]);

  useEffect(() => {
    load();
  }, [load]);

  const setParam = (key, value) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next);
  };

  const title = group
    ? GROUP_LABELS[group] || group
    : search
    ? `Resultados para "${search}"`
    : badge
    ? badge
    : onSale
    ? "Promoções"
    : "Todos os produtos";

  return (
    <div className="max-w-[1400px] mx-auto px-4 lg:px-8 py-10">
      <div className="bm-stripe rounded-full max-w-[120px] mb-5" />
      <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl lg:text-5xl font-display font-black uppercase tracking-tight text-white" data-testid="catalog-title">
            {title}
          </h1>
          <p className="text-gray-500 mt-2">{total} produto(s) encontrado(s)</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="lg:hidden flex items-center gap-2 bm-card px-4 py-2.5 text-sm text-white"
          >
            <SlidersHorizontal size={16} /> Filtros
          </button>
          <select
            data-testid="sort-select"
            value={sort}
            onChange={(e) => setParam("sort", e.target.value)}
            className="bm-card px-4 py-2.5 text-sm text-white bg-[#1f1f1f] focus:outline-none focus:border-[#1E3A8A]"
          >
            {SORTS.map((s) => (
              <option key={s.v} value={s.v}>{s.l}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="flex gap-8">
        {/* Filters */}
        <aside className={`${showFilters ? "block" : "hidden"} lg:block w-full lg:w-64 shrink-0`}>
          <div className="bm-card p-5 sticky top-28">
            <div className="flex items-center justify-between lg:hidden mb-4">
              <span className="font-semibold text-white">Filtros</span>
              <button onClick={() => setShowFilters(false)}><X size={18} className="text-white" /></button>
            </div>

            <FilterGroup title="Categorias">
              <FilterItem active={!category} onClick={() => setParam("category", "")} label="Todas" />
              {categories.map((c) => (
                <FilterItem
                  key={c.id}
                  active={category === c.slug}
                  onClick={() => setParam("category", c.slug)}
                  label={c.name}
                />
              ))}
            </FilterGroup>

            <FilterGroup title="Marcas">
              <FilterItem active={!brand} onClick={() => setParam("brand", "")} label="Todas" />
              {brands.map((b) => (
                <FilterItem
                  key={b.id}
                  active={brand === b.slug}
                  onClick={() => setParam("brand", b.slug)}
                  label={b.name}
                />
              ))}
            </FilterGroup>

            <FilterGroup title="Ofertas">
              <FilterItem active={!!onSale} onClick={() => setParam("on_sale", onSale ? "" : "true")} label="Somente promoções" />
            </FilterGroup>
          </div>
        </aside>

        {/* Grid */}
        <div className="flex-1">
          {loading ? (
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 lg:gap-6">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="bm-card aspect-[3/4] animate-pulse" />
              ))}
            </div>
          ) : products.length === 0 ? (
            <div className="bm-card p-16 text-center">
              <p className="text-gray-400">Nenhum produto encontrado com os filtros selecionados.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 lg:gap-6" data-testid="products-grid">
              {products.map((p, i) => (
                <ProductCard key={p.id} product={p} index={i} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function FilterGroup({ title, children }) {
  return (
    <div className="mb-6 last:mb-0">
      <h4 className="text-xs uppercase tracking-widest text-[#FFC107] font-bold mb-3">{title}</h4>
      <div className="space-y-1 max-h-64 overflow-y-auto pr-1">{children}</div>
    </div>
  );
}

function FilterItem({ active, onClick, label }) {
  return (
    <button
      onClick={onClick}
      className={`block w-full text-left text-sm px-3 py-1.5 rounded-lg transition-colors ${
        active ? "bg-[#1E3A8A] text-white" : "text-gray-400 hover:text-white hover:bg-white/5"
      }`}
    >
      {label}
    </button>
  );
}
