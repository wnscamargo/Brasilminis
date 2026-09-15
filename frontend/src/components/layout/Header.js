import { useState, useRef, useEffect, useLayoutEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Search, Heart, ShoppingCart, User, Menu, X, ChevronDown, ChevronRight } from "lucide-react";
import BrandLogo from "@/components/BrandLogo";
import { useCart } from "@/context/CartContext";
import { useAuth } from "@/context/AuthContext";
import { useFavorites } from "@/context/FavoritesContext";
import { useCategories } from "@/context/CategoriesContext";

// Itens institucionais fixos (NÃO são categorias) — mantidos separados das categorias dinâmicas.
const INSTITUTIONAL_LEFT = [{ label: "Início", to: "/" }];
const INSTITUTIONAL_RIGHT = [
  { label: "Lançamentos", to: "/produtos?badge=LANÇAMENTO" },
  { label: "Promoções", to: "/produtos?on_sale=true" },
  { label: "Marcas", to: "/marcas" },
  { label: "Contato", to: "/contato" },
];

const slugTest = (s) => (s || "").replace(/[^a-z0-9]/g, "");

export default function Header() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const { count } = useCart();
  const { user } = useAuth();
  const { ids } = useFavorites();
  const { tree } = useCategories();
  const navigate = useNavigate();

  const submitSearch = (e) => {
    e.preventDefault();
    if (q.trim()) navigate(`/produtos?search=${encodeURIComponent(q.trim())}`);
  };

  return (
    <header className="sticky top-0 z-50">
      <div className="bm-stripe" />
      <div className="bm-glass">
        <div className="max-w-[1400px] mx-auto px-4 lg:px-8">
          {/* top row */}
          <div className="flex items-center gap-4 h-20 md:h-24">
            <button className="lg:hidden text-white" onClick={() => setOpen(!open)} data-testid="mobile-menu-toggle" aria-label="Menu" aria-expanded={open}>
              {open ? <X size={26} /> : <Menu size={26} />}
            </button>

            <Link to="/" data-testid="logo-link" className="shrink-0 inline-flex items-start" aria-label="Brasil Minis® | Miniaturas Diecast">
              <BrandLogo variant="header" />
              <sup className="text-gray-400 text-[10px] ml-0.5 mt-1 select-none">®</sup>
            </Link>

            <form onSubmit={submitSearch} className="hidden md:flex flex-1 max-w-xl mx-4 relative">
              <input
                data-testid="search-input"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Buscar miniaturas, marcas, acessórios..."
                className="w-full bg-[#1f1f1f] border border-[#2e2e2e] rounded-full py-2.5 pl-5 pr-12 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:border-[#1E3A8A] transition-colors"
              />
              <button type="submit" data-testid="search-submit" className="absolute right-1.5 top-1.5 h-8 w-8 grid place-items-center rounded-full bg-[#1E3A8A] text-white hover:bg-[#152b66] transition-colors">
                <Search size={16} />
              </button>
            </form>

            <div className="flex items-center gap-1 md:gap-2 ml-auto">
              <Link to={user ? "/conta" : "/login"} data-testid="account-link" className="flex items-center gap-2 px-3 py-2 rounded-full text-gray-200 hover:bg-white/5 transition-colors">
                <User size={22} />
                <span className="hidden xl:inline text-sm">{user ? user.name.split(" ")[0] : "Entrar"}</span>
              </Link>
              <Link to="/favoritos" data-testid="favorites-link" className="relative p-2 rounded-full text-gray-200 hover:bg-white/5 transition-colors">
                <Heart size={22} />
                {ids.length > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 bg-[#009B3A] text-white text-[10px] font-bold rounded-full h-4 min-w-4 px-1 grid place-items-center">{ids.length}</span>
                )}
              </Link>
              <Link to="/carrinho" data-testid="cart-link" className="relative p-2 rounded-full text-gray-200 hover:bg-white/5 transition-colors">
                <ShoppingCart size={22} />
                {count > 0 && (
                  <span data-testid="cart-count" className="absolute -top-0.5 -right-0.5 bg-[#FFC107] text-[#111111] text-[10px] font-bold rounded-full h-4 min-w-4 px-1 grid place-items-center">{count}</span>
                )}
              </Link>
            </div>
          </div>

          {/* nav row (desktop) — categorias dinâmicas com overflow "MAIS" */}
          <DesktopNav tree={tree} />
        </div>
      </div>

      {/* mobile menu */}
      {open && (
        <div className="lg:hidden bg-[#1f1f1f] border-b border-[#2e2e2e] px-4 py-4 max-h-[80vh] overflow-y-auto overflow-x-hidden" data-testid="mobile-nav">
          <form onSubmit={submitSearch} className="relative mb-4">
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Buscar..." className="w-full bg-[#111111] border border-[#2e2e2e] rounded-full py-2.5 pl-4 pr-12 text-sm text-white" />
            <button type="submit" className="absolute right-1.5 top-1.5 h-8 w-8 grid place-items-center rounded-full bg-[#1E3A8A] text-white"><Search size={16} /></button>
          </form>

          {INSTITUTIONAL_LEFT.map((m) => (
            <Link key={m.label} to={m.to} onClick={() => setOpen(false)} className="block px-2 py-2.5 text-sm uppercase tracking-wide font-medium text-gray-200 hover:text-[#FFC107]">{m.label}</Link>
          ))}

          <div className="my-2 border-t border-[#2e2e2e]" />
          {tree.map((cat) => (
            <MobileCategory key={cat.id} cat={cat} close={() => setOpen(false)} />
          ))}
          <div className="my-2 border-t border-[#2e2e2e]" />

          {INSTITUTIONAL_RIGHT.map((m) => (
            <Link key={m.label} to={m.to} onClick={() => setOpen(false)} className="block px-2 py-2.5 text-sm uppercase tracking-wide font-medium text-gray-200 hover:text-[#FFC107]">{m.label}</Link>
          ))}
        </div>
      )}
    </header>
  );
}

// -------- Desktop nav com cálculo de overflow por espaço disponível --------
function DesktopNav({ tree }) {
  const rowRef = useRef(null);
  const startRef = useRef(null);
  const rightRef = useRef(null);
  const measureRef = useRef(null);
  const [visibleCount, setVisibleCount] = useState(tree.length);
  const [openKey, setOpenKey] = useState(null); // slug do dropdown aberto (inclui "__more__")

  const closeAll = useCallback(() => setOpenKey(null), []);

  // Recalcula quantas categorias cabem, com base no espaço real disponível.
  const recompute = useCallback(() => {
    const row = rowRef.current, start = startRef.current, right = rightRef.current, meas = measureRef.current;
    if (!row || !start || !right || !meas) return;
    const GAP = 4;
    const containerW = row.clientWidth;
    const startW = start.offsetWidth;
    const rightW = right.offsetWidth;
    const catEls = Array.from(meas.querySelectorAll("[data-measure-cat]"));
    const catWidths = catEls.map((el) => el.getBoundingClientRect().width + GAP);
    const moreEl = meas.querySelector("[data-measure-more]");
    const moreW = (moreEl ? moreEl.getBoundingClientRect().width : 80) + GAP;
    const totalCats = catWidths.reduce((a, b) => a + b, 0);

    if (startW + rightW + totalCats <= containerW) {
      setVisibleCount(tree.length);
      return;
    }
    const avail = containerW - startW - rightW - moreW;
    let used = 0, n = 0;
    for (const w of catWidths) {
      if (used + w <= avail) { used += w; n += 1; } else break;
    }
    setVisibleCount(Math.max(0, n));
  }, [tree.length]);

  useLayoutEffect(() => {
    recompute();
    const ro = new ResizeObserver(recompute);
    if (rowRef.current) ro.observe(rowRef.current);
    window.addEventListener("resize", recompute);
    return () => { ro.disconnect(); window.removeEventListener("resize", recompute); };
  }, [recompute, tree]);

  // Fecha dropdown ao clicar fora / ESC.
  useEffect(() => {
    if (!openKey) return;
    const onDocClick = (e) => { if (rowRef.current && !rowRef.current.contains(e.target)) closeAll(); };
    const onKey = (e) => { if (e.key === "Escape") closeAll(); };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => { document.removeEventListener("mousedown", onDocClick); document.removeEventListener("keydown", onKey); };
  }, [openKey, closeAll]);

  const visible = tree.slice(0, visibleCount);
  const overflow = tree.slice(visibleCount);

  return (
    <>
      {/* Linha de medição invisível (mesmos estilos) para calcular larguras reais */}
      <nav ref={measureRef} aria-hidden="true" className="hidden lg:flex items-center gap-1 absolute opacity-0 pointer-events-none -z-10" style={{ left: -9999, top: 0 }}>
        {tree.map((cat) => (
          <span key={cat.id} data-measure-cat className="flex items-center gap-1 px-3 py-1.5 text-[13px] uppercase tracking-wide font-medium">
            {cat.name}{(cat.children || []).length > 0 && <ChevronDown size={14} />}
          </span>
        ))}
        <span data-measure-more className="flex items-center gap-1 px-3 py-1.5 text-[13px] uppercase tracking-wide font-medium">Mais<ChevronDown size={14} /></span>
      </nav>

      <nav ref={rowRef} className="hidden lg:flex items-center gap-1 pb-3 -mt-1 flex-nowrap overflow-visible" data-testid="desktop-nav">
        <span ref={startRef} className="flex items-center gap-1 shrink-0">
          {INSTITUTIONAL_LEFT.map((m) => <NavLink key={m.label} to={m.to} label={m.label} />)}
        </span>

        <span className="flex items-center gap-1 min-w-0">
          {visible.map((cat) => (
            <CategoryMenuItem key={cat.id} cat={cat} openKey={openKey} setOpenKey={setOpenKey} />
          ))}
          {overflow.length > 0 && (
            <MoreMenu items={overflow} openKey={openKey} setOpenKey={setOpenKey} />
          )}
        </span>

        <span ref={rightRef} className="flex items-center gap-1 shrink-0 ml-auto">
          {INSTITUTIONAL_RIGHT.map((m) => <NavLink key={m.label} to={m.to} label={m.label} />)}
        </span>
      </nav>
    </>
  );
}

function NavLink({ to, label }) {
  return (
    <Link to={to} data-testid={`nav-${label.toLowerCase().replace(/[^a-z]/g, "")}`} className="px-3 py-1.5 text-[13px] uppercase tracking-wide font-medium text-gray-300 hover:text-[#FFC107] transition-colors whitespace-nowrap">
      {label}
    </Link>
  );
}

// Desktop: categoria raiz clicável + dropdown de subcategorias (hover + clique + teclado).
function CategoryMenuItem({ cat, openKey, setOpenKey }) {
  const kids = cat.children || [];
  const key = cat.slug;
  const st = slugTest(cat.slug);
  const isOpen = openKey === key;
  const wrapRef = useRef(null);
  const closeTimer = useRef(null);

  const openNow = () => { clearTimeout(closeTimer.current); if (kids.length) setOpenKey(key); };
  const closeSoon = () => { clearTimeout(closeTimer.current); closeTimer.current = setTimeout(() => setOpenKey((k) => (k === key ? null : k)), 120); };

  const onKeyDown = (e) => {
    if (!kids.length) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setOpenKey(key);
      // aguarda o dropdown montar para então focar o primeiro item (mesmo ArrowDown)
      requestAnimationFrame(() => wrapRef.current?.querySelector("[data-dd-item]")?.focus());
    }
  };
  const onItemKey = (e) => {
    const items = Array.from(wrapRef.current?.querySelectorAll("[data-dd-item]") || []);
    const i = items.indexOf(document.activeElement);
    if (e.key === "ArrowDown") { e.preventDefault(); items[Math.min(i + 1, items.length - 1)]?.focus(); }
    else if (e.key === "ArrowUp") { e.preventDefault(); if (i <= 0) return; items[i - 1]?.focus(); }
  };

  return (
    <div ref={wrapRef} className="relative shrink-0" data-testid={`nav-cat-${st}`} onMouseEnter={openNow} onMouseLeave={closeSoon}>
      <Link
        to={`/produtos?category=${cat.slug}`}
        data-testid={`nav-cat-link-${st}`}
        aria-haspopup={kids.length ? "menu" : undefined}
        aria-expanded={kids.length ? isOpen : undefined}
        onKeyDown={onKeyDown}
        onClick={() => kids.length && setOpenKey(isOpen ? null : key)}
        className="flex items-center gap-1 px-3 py-1.5 text-[13px] uppercase tracking-wide font-medium text-gray-300 hover:text-[#FFC107] transition-colors whitespace-nowrap"
      >
        {cat.name}
        {kids.length > 0 && <ChevronDown size={14} className={`opacity-70 transition-transform ${isOpen ? "rotate-180" : ""}`} />}
      </Link>
      {kids.length > 0 && isOpen && (
        <div className="absolute left-0 top-full pt-2 z-50" data-testid={`nav-dropdown-${st}`} role="menu" onKeyDown={onItemKey}>
          <div className="min-w-[220px] max-w-[280px] bg-[#1f1f1f] border border-[#2e2e2e] rounded-xl shadow-2xl py-2">
            <Link to={`/produtos?category=${cat.slug}`} data-dd-item role="menuitem" onClick={() => setOpenKey(null)} className="block px-4 py-2 text-xs uppercase tracking-wider text-[#FFC107] font-bold hover:bg-white/5 focus:bg-white/10 outline-none">
              Ver tudo de {cat.name}
            </Link>
            <div className="my-1 border-t border-[#2e2e2e]" />
            {kids.map((sub) => (
              <Link
                key={sub.id}
                to={`/produtos?category=${sub.slug}`}
                data-dd-item
                role="menuitem"
                data-testid={`nav-sub-link-${slugTest(sub.slug)}`}
                onClick={() => setOpenKey(null)}
                className="block px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-white/5 focus:bg-white/10 outline-none transition-colors"
              >
                {sub.name}
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Menu "MAIS" — recebe as categorias que não couberam (calculado por espaço).
function MoreMenu({ items, openKey, setOpenKey }) {
  const key = "__more__";
  const isOpen = openKey === key;
  const wrapRef = useRef(null);
  const closeTimer = useRef(null);
  const openNow = () => { clearTimeout(closeTimer.current); setOpenKey(key); };
  const closeSoon = () => { clearTimeout(closeTimer.current); closeTimer.current = setTimeout(() => setOpenKey((k) => (k === key ? null : k)), 120); };

  return (
    <div ref={wrapRef} className="relative shrink-0" data-testid="nav-more" onMouseEnter={openNow} onMouseLeave={closeSoon}>
      <button
        aria-haspopup="menu"
        aria-expanded={isOpen}
        data-testid="nav-more-btn"
        onClick={() => setOpenKey(isOpen ? null : key)}
        className="flex items-center gap-1 px-3 py-1.5 text-[13px] uppercase tracking-wide font-medium text-gray-300 hover:text-[#FFC107] transition-colors whitespace-nowrap"
      >
        Mais <ChevronDown size={14} className={`opacity-70 transition-transform ${isOpen ? "rotate-180" : ""}`} />
      </button>
      {isOpen && (
        <div className="absolute right-0 top-full pt-2 z-50" data-testid="nav-more-dropdown" role="menu">
          <div className="min-w-[240px] max-w-[300px] max-h-[70vh] overflow-y-auto bg-[#1f1f1f] border border-[#2e2e2e] rounded-xl shadow-2xl py-2">
            {items.map((cat) => (
              <div key={cat.id} className="py-1">
                <Link to={`/produtos?category=${cat.slug}`} role="menuitem" onClick={() => setOpenKey(null)} data-testid={`more-cat-link-${slugTest(cat.slug)}`} className="block px-4 py-1.5 text-sm uppercase tracking-wide font-semibold text-white hover:text-[#FFC107] focus:bg-white/10 outline-none">
                  {cat.name}
                </Link>
                {(cat.children || []).map((sub) => (
                  <Link key={sub.id} to={`/produtos?category=${sub.slug}`} role="menuitem" onClick={() => setOpenKey(null)} className="block px-6 py-1.5 text-sm text-gray-400 hover:text-white hover:bg-white/5 focus:bg-white/10 outline-none">
                    {sub.name}
                  </Link>
                ))}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Mobile: acordeão touch-friendly por categoria.
function MobileCategory({ cat, close }) {
  const [expanded, setExpanded] = useState(false);
  const kids = cat.children || [];
  const st = slugTest(cat.slug);
  return (
    <div className="border-b border-[#2e2e2e]/50 last:border-0">
      <div className="flex items-center">
        <Link
          to={`/produtos?category=${cat.slug}`}
          onClick={close}
          data-testid={`mnav-cat-link-${st}`}
          className="flex-1 px-2 py-3 text-sm uppercase tracking-wide font-semibold text-white hover:text-[#FFC107] break-words"
        >
          {cat.name}
        </Link>
        {kids.length > 0 && (
          <button
            onClick={() => setExpanded((v) => !v)}
            data-testid={`mnav-toggle-${st}`}
            aria-label={`Expandir ${cat.name}`}
            aria-expanded={expanded}
            className="p-3 text-gray-400"
          >
            {expanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
          </button>
        )}
      </div>
      {expanded && kids.length > 0 && (
        <div className="pb-2 pl-4">
          {kids.map((sub) => (
            <Link
              key={sub.id}
              to={`/produtos?category=${sub.slug}`}
              onClick={close}
              data-testid={`mnav-sub-link-${slugTest(sub.slug)}`}
              className="block px-2 py-2 text-sm text-gray-400 hover:text-white break-words"
            >
              {sub.name}
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
