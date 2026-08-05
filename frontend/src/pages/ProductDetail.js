import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Heart, ShoppingCart, Star, Truck, ShieldCheck, Minus, Plus, ChevronRight } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { badgeClass, formatBRL } from "@/lib/brand";
import { useCart } from "@/context/CartContext";
import { useFavorites } from "@/context/FavoritesContext";
import { useAuth } from "@/context/AuthContext";
import ProductCard from "@/components/ProductCard";

export default function ProductDetail() {
  const { slug } = useParams();
  const [product, setProduct] = useState(null);
  const [related, setRelated] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [activeImg, setActiveImg] = useState(0);
  const [qty, setQty] = useState(1);
  const [tab, setTab] = useState("desc");
  const [rForm, setRForm] = useState({ rating: 5, comment: "" });

  const { addItem } = useCart();
  const { ids, toggle } = useFavorites();
  const { user } = useAuth();

  useEffect(() => {
    window.scrollTo(0, 0);
    setActiveImg(0);
    setQty(1);
    (async () => {
      try {
        const { data } = await api.get(`/products/${slug}`);
        setProduct(data);
        const [rel, rev] = await Promise.all([
          api.get(`/products/${slug}/related`),
          api.get(`/products/${data.id}/reviews`),
        ]);
        setRelated(rel.data);
        setReviews(rev.data);
      } catch {
        setProduct(false);
      }
    })();
  }, [slug]);

  if (product === false)
    return (
      <div className="max-w-[1400px] mx-auto px-4 py-24 text-center text-gray-400">
        Produto não encontrado. <Link to="/produtos" className="text-[#FFC107]">Voltar ao catálogo</Link>
      </div>
    );
  if (!product)
    return (
      <div className="min-h-[60vh] grid place-items-center">
        <div className="h-10 w-10 rounded-full border-2 border-[#2e2e2e] border-t-[#FFC107] animate-spin" />
      </div>
    );

  const isFav = ids.includes(product.id);
  const discount =
    product.compare_at_price && product.compare_at_price > product.price
      ? Math.round((1 - product.price / product.compare_at_price) * 100)
      : 0;

  const submitReview = async (e) => {
    e.preventDefault();
    if (!user) return toast.error("Entre para avaliar este produto");
    try {
      await api.post(`/products/${product.id}/reviews`, rForm);
      const rev = await api.get(`/products/${product.id}/reviews`);
      setReviews(rev.data);
      setRForm({ rating: 5, comment: "" });
      toast.success("Avaliação enviada!");
    } catch {
      toast.error("Não foi possível enviar a avaliação");
    }
  };

  return (
    <div className="max-w-[1400px] mx-auto px-4 lg:px-8 py-8">
      {/* breadcrumb */}
      <nav className="flex items-center gap-1.5 text-xs text-gray-500 mb-6 flex-wrap">
        <Link to="/" className="hover:text-white">Início</Link>
        <ChevronRight size={13} />
        <Link to={`/grupo/${product.group}`} className="hover:text-white capitalize">{product.group}</Link>
        <ChevronRight size={13} />
        <span className="text-gray-300">{product.name}</span>
      </nav>

      <div className="grid lg:grid-cols-2 gap-10">
        {/* gallery */}
        <div>
          <motion.div
            key={activeImg}
            initial={{ opacity: 0.4 }}
            animate={{ opacity: 1 }}
            className="bm-card overflow-hidden aspect-square group"
          >
            <img
              src={product.images?.[activeImg]}
              alt={product.name}
              className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110 cursor-zoom-in"
              data-testid="product-main-image"
            />
          </motion.div>
          {product.images?.length > 1 && (
            <div className="flex gap-3 mt-3">
              {product.images.map((img, i) => (
                <button
                  key={i}
                  onClick={() => setActiveImg(i)}
                  className={`h-20 w-20 rounded-lg overflow-hidden border-2 transition-colors ${
                    activeImg === i ? "border-[#FFC107]" : "border-[#2e2e2e]"
                  }`}
                >
                  <img src={img} alt="" className="h-full w-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* info */}
        <div>
          {product.brand && (
            <span className="text-xs uppercase tracking-[0.25em] text-[#1E3A8A] font-bold">
              {product.brand.replace(/-/g, " ")}
            </span>
          )}
          <h1 className="text-3xl lg:text-4xl font-display font-black uppercase tracking-tight text-white mt-2">
            {product.name}
          </h1>

          <div className="flex flex-wrap items-center gap-2 mt-4">
            {(product.badges || []).map((b) => (
              <span key={b} className={`px-3 py-1 text-[11px] font-bold uppercase tracking-wider rounded-full ${badgeClass(b)}`}>
                {b}
              </span>
            ))}
          </div>

          {product.reviews_count > 0 && (
            <div className="flex items-center gap-1.5 mt-4 text-[#FFC107]">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star key={i} size={16} fill={i < Math.round(product.rating) ? "currentColor" : "none"} />
              ))}
              <span className="text-sm text-gray-400 ml-1">{product.rating} · {product.reviews_count} avaliações</span>
            </div>
          )}

          <div className="mt-6 flex items-end gap-3">
            {discount > 0 && (
              <span className="text-lg text-gray-500 line-through">{formatBRL(product.compare_at_price)}</span>
            )}
            <span className="text-4xl font-display font-black text-white">{formatBRL(product.price)}</span>
            {discount > 0 && (
              <span className="mb-1.5 px-2 py-1 text-xs font-bold rounded-full bg-[#FFC107] text-[#111111]">-{discount}%</span>
            )}
          </div>
          <p className="text-sm text-gray-500 mt-1">Em até 12x no cartão ou PIX à vista</p>

          <p className="text-gray-300 mt-6 leading-relaxed">{product.description}</p>

          <div className="mt-6 flex items-center gap-4">
            <div className="flex items-center bm-card">
              <button onClick={() => setQty(Math.max(1, qty - 1))} className="p-3 text-white hover:text-[#FFC107]" data-testid="qty-minus">
                <Minus size={16} />
              </button>
              <span className="w-10 text-center text-white font-semibold" data-testid="qty-value">{qty}</span>
              <button onClick={() => setQty(Math.min(product.stock, qty + 1))} className="p-3 text-white hover:text-[#FFC107]" data-testid="qty-plus">
                <Plus size={16} />
              </button>
            </div>
            <span className={`text-sm ${product.stock > 0 ? "text-[#009B3A]" : "text-red-400"}`}>
              {product.stock > 0 ? `${product.stock} em estoque` : "Esgotado"}
            </span>
          </div>

          <div className="mt-6 flex flex-wrap gap-3">
            <button
              onClick={() => { addItem(product, qty); }}
              disabled={product.stock <= 0}
              data-testid="buy-now-btn"
              className="flex-1 min-w-[180px] bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full px-8 py-4 hover:bg-[#e0a800] transition-colors shadow-[0_0_20px_rgba(255,193,7,0.3)] disabled:opacity-40 flex items-center justify-center gap-2"
            >
              <ShoppingCart size={18} /> Comprar Agora
            </button>
            <button
              onClick={() => toggle(product)}
              data-testid="detail-fav-btn"
              className={`h-14 w-14 grid place-items-center rounded-full border transition-colors ${
                isFav ? "bg-[#009B3A] border-[#009B3A] text-white" : "bg-[#111111] border-white text-white hover:bg-white/10"
              }`}
            >
              <Heart size={20} fill={isFav ? "currentColor" : "none"} />
            </button>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-8">
            <div className="bm-card p-4 flex items-center gap-3">
              <Truck className="text-[#FFC107]" size={22} />
              <span className="text-xs text-gray-300">Entrega para todo o Brasil</span>
            </div>
            <div className="bm-card p-4 flex items-center gap-3">
              <ShieldCheck className="text-[#FFC107]" size={22} />
              <span className="text-xs text-gray-300">Produto 100% original</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mt-16">
        <div className="flex gap-2 border-b border-[#2e2e2e]">
          {[["desc", "Descrição"], ["specs", "Especificações"], ["reviews", `Avaliações (${reviews.length})`]].map(([k, l]) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              className={`px-5 py-3 text-sm font-semibold uppercase tracking-wide transition-colors ${
                tab === k ? "text-[#FFC107] border-b-2 border-[#FFC107]" : "text-gray-400 hover:text-white"
              }`}
            >
              {l}
            </button>
          ))}
        </div>

        <div className="py-8">
          {tab === "desc" && <p className="text-gray-300 leading-relaxed max-w-3xl">{product.description}</p>}

          {tab === "specs" && (
            <div className="max-w-2xl bm-honeycomb rounded-xl overflow-hidden">
              {Object.keys(product.specs || {}).length === 0 ? (
                <p className="text-gray-500 p-5">Especificações não informadas.</p>
              ) : (
                Object.entries(product.specs).map(([k, v], i) => (
                  <div key={k} className={`flex justify-between px-5 py-3 ${i % 2 ? "bg-black/20" : ""}`}>
                    <span className="text-gray-400">{k}</span>
                    <span className="text-white font-medium">{v}</span>
                  </div>
                ))
              )}
            </div>
          )}

          {tab === "reviews" && (
            <div className="grid lg:grid-cols-2 gap-8">
              <div className="space-y-4">
                {reviews.length === 0 && <p className="text-gray-500">Seja o primeiro a avaliar.</p>}
                {reviews.map((r) => (
                  <div key={r.id} className="bm-card p-5">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-white">{r.user_name}</span>
                      <div className="flex text-[#FFC107]">
                        {Array.from({ length: 5 }).map((_, i) => (
                          <Star key={i} size={14} fill={i < r.rating ? "currentColor" : "none"} />
                        ))}
                      </div>
                    </div>
                    <p className="text-gray-400 text-sm mt-2">{r.comment}</p>
                  </div>
                ))}
              </div>
              <form onSubmit={submitReview} className="bm-card p-6 h-fit">
                <h4 className="font-display font-bold text-white uppercase mb-4">Deixe sua avaliação</h4>
                <div className="flex gap-1 mb-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <button type="button" key={i} onClick={() => setRForm({ ...rForm, rating: i + 1 })}>
                      <Star size={26} className="text-[#FFC107]" fill={i < rForm.rating ? "currentColor" : "none"} />
                    </button>
                  ))}
                </div>
                <textarea
                  value={rForm.comment}
                  onChange={(e) => setRForm({ ...rForm, comment: e.target.value })}
                  rows={4}
                  required
                  placeholder="Conte o que achou do produto..."
                  className="w-full bg-[#111111] border border-[#2e2e2e] rounded-xl p-3 text-sm text-white focus:outline-none focus:border-[#1E3A8A]"
                />
                <button className="mt-3 bg-[#1E3A8A] text-white font-semibold rounded-full px-6 py-3 hover:bg-[#152b66] transition-colors">
                  Enviar avaliação
                </button>
              </form>
            </div>
          )}
        </div>
      </div>

      {/* related */}
      {related.length > 0 && (
        <div className="mt-16">
          <h2 className="text-2xl lg:text-3xl font-display font-black uppercase text-white mb-8">Produtos relacionados</h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
            {related.slice(0, 4).map((p, i) => (
              <ProductCard key={p.id} product={p} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
