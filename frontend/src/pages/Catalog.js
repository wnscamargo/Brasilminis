import { useEffect, useState, useCallback } from "react";
import { useSearchParams, useParams, Link } from "react-router-dom";
import { SlidersHorizontal, X, ChevronDown, ChevronRight } from "lucide-react";
import api from "@/lib/api";
import { GROUP_LABELS } from "@/lib/brand";
import ProductCard from "@/components/ProductCard";
import { useCategories, findCategoryTrail } from "@/context/CategoriesContext";

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
  const { tree } = useCategories();
  const [products, setProducts] = useState([]);
  const [total, setTotal] = useState(0);
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

  // Só mexe no param informado — preserva os demais (marca, promoção, ordenação).
  const setParam = (key, value) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value);
    else next.delete(key);
    setParams(next);
  };

  // "Todas": limpa APENAS a categoria (mantém marca/promoção/ordenação).
  const clearCategory = () => setParam("category", "");

  const trail = findCategoryTrail(tree, category);

  return (
    <div className="max-w-[1400px] mx-auto px-4 lg:px-8 py-10">
      <div className="bm-stripe rounded-full max-w-[120px] mb-5" />
      <div className="flex flex-wrap items-end justify-between gap-4 mb-8">
        <div>
          <CatalogHeading trail={trail} group={group} search={search} badge={badge} onSale={onSale} />
          <p className="text-gray-500 mt-2">{total} produto(s) encontrado(s)</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={() => setShowFilters(!showFilters)} className="lg:hidden flex items-center gap-2 bm-card px-4 py-2.5 text-sm text-white">
            <SlidersHorizontal size={16} /> Filtros
          </button>
          <select data-testid="sort-select" value={sort} onChange={(e) => setParam("sort", e.target.value)} className="bm-card px-4 py-2.5 text-sm text-white bg-[#1f1f1f] focus:outline-none focus:border-[#1E3A8A]">
            {SORTS.map((s) => (<option key={s.v} value={s.v}>{s.l}</option>))}
          </select>
        </div>
      </div>

      <div className="flex gap-8">
        {/* Filters */}
        <aside className={`${showFilters ? "block" : "hidden"} lg:block w-full lg:w-72 shrink-0`}>
          <div className="bm-card p-5 sticky top-28">
            <div className="flex items-center justify-between lg:hidden mb-4">
              <span className="font-semibold text-white">Filtros</span>
              <button onClick={() => setShowFilters(false)}><X size={18} className="text-white" /></button>
            </div>

            <FilterGroup title="Categorias">
              <FilterItem active={!category} onClick={clearCategory} label="Todas" testid="filter-cat-todas" />
              {tree.map((cat) => (
                <CategoryFilterNode
                  key={cat.id}
                  cat={cat}
                  activeSlug={category}
                  onSelect={(slug) => setParam("category", slug)}
                />
              ))}
            </FilterGroup>

            <FilterGroup title="Marcas">
              <FilterItem active={!brand} onClick={() => setParam("brand", "")} label="Todas" />
              {brands.map((b) => (
                <FilterItem key={b.id} active={brand === b.slug} onClick={() => setParam("brand", b.slug)} label={b.name} />
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
              {Array.from({ length: 8 }).map((_, i) => (<div key={i} className="bm-card aspect-[3/4] animate-pulse" />))}
            </div>
          ) : products.length === 0 ? (
            <div className="bm-card p-16 text-center">
              <p className="text-gray-400">Nenhum produto encontrado com os filtros selecionados.</p>
            </div>
          ) : (
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 lg:gap-6" data-testid="products-grid">
              {products.map((p, i) => (<ProductCard key={p.id} product={p} index={i} />))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function CatalogHeading({ trail, group, search, badge, onSale }) {
  if (trail) {
    return (
      <div data-testid="catalog-header">
        <nav className="flex items-center gap-2 text-xs uppercase tracking-widest text-gray-500 mb-2" data-testid="catalog-breadcrumb">
          <Link to={`/produtos?category=${trail.main.slug}`} className="hover:text-[#FFC107]">{trail.main.name}</Link>
          {trail.sub && (<><ChevronRight size={12} /><span className="text-[#FFC107]">{trail.sub.name}</span></>)}
        </nav>
        <h1 className="text-3xl lg:text-5xl font-display font-black uppercase tracking-tight text-white" data-testid="catalog-title">
          {trail.sub ? trail.sub.name : trail.main.name}
        </h1>
      </div>
    );
  }
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
    <h1 className="text-3xl lg:text-5xl font-display font-black uppercase tracking-tight text-white" data-testid="catalog-title">
      {title}
    </h1>
  );
}

function FilterGroup({ title, children }) {
  return (
    <div className="mb-6 last:mb-0">
      <h4 className="text-xs uppercase tracking-widest text-[#FFC107] font-bold mb-3">{title}</h4>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

// Accordion de categoria principal + subcategorias (sem limite de altura/scroll).
function CategoryFilterNode({ cat, activeSlug, onSelect }) {
  const kids = cat.children || [];
  const childActive = kids.some((k) => k.slug === activeSlug);
  const [expanded, setExpanded] = useState(childActive);
  const slugTest = cat.slug.replace(/[^a-z0-9]/g, "");
  return (
    <div>
      <div className="flex items-center">
        <button
          onClick={() => onSelect(cat.slug)}
          data-testid={`filter-cat-${slugTest}`}
          className={`flex-1 text-left text-sm px-3 py-1.5 rounded-lg transition-colors ${
            activeSlug === cat.slug ? "bg-[#1E3A8A] text-white" : "text-gray-300 hover:text-white hover:bg-white/5"
          } font-semibold`}
        >
          {cat.name}
        </button>
        {kids.length > 0 && (
          <button onClick={() => setExpanded((v) => !v)} data-testid={`filter-toggle-${slugTest}`} aria-label={`Expandir ${cat.name}`} className="p-1.5 text-gray-500 hover:text-white">
            {expanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </button>
        )}
      </div>
      {expanded && kids.length > 0 && (
        <div className="ml-3 mt-1 border-l border-[#2e2e2e] pl-2 space-y-1">
          {kids.map((sub) => (
            <FilterItem
              key={sub.id}
              active={activeSlug === sub.slug}
              onClick={() => onSelect(sub.slug)}
              label={sub.name}
              testid={`filter-sub-${sub.slug.replace(/[^a-z0-9]/g, "")}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function FilterItem({ active, onClick, label, testid }) {
  return (
    <button
      onClick={onClick}
      data-testid={testid}
      className={`block w-full text-left text-sm px-3 py-1.5 rounded-lg transition-colors ${
        active ? "bg-[#1E3A8A] text-white" : "text-gray-400 hover:text-white hover:bg-white/5"
      }`}
    >
      {label}
    </button>
  );
}
