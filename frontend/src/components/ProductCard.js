import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Heart, Star } from "lucide-react";
import { badgeClass, formatBRL } from "@/lib/brand";
import { useCart } from "@/context/CartContext";
import { useFavorites } from "@/context/FavoritesContext";

export default function ProductCard({ product, index = 0 }) {
  const { addItem } = useCart();
  const { ids, toggle } = useFavorites();
  const isFav = ids.includes(product.id);
  const discount =
    product.compare_at_price && product.compare_at_price > product.price
      ? Math.round((1 - product.price / product.compare_at_price) * 100)
      : 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.4, delay: (index % 4) * 0.06 }}
      className="group bm-card overflow-hidden flex flex-col hover:border-[#1E3A8A] transition-colors duration-300"
      data-testid={`product-card-${product.id}`}
    >
      <div className="relative aspect-square overflow-hidden bg-[#171717]">
        <Link to={`/produto/${product.slug}`}>
          <img
            src={product.images?.[0]}
            alt={product.name}
            loading="lazy"
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
          />
        </Link>

        <div className="absolute top-3 left-3 flex flex-col gap-1.5 max-w-[70%]">
          {(product.badges || []).slice(0, 2).map((b) => (
            <span
              key={b}
              className={`px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full ${badgeClass(b)}`}
            >
              {b}
            </span>
          ))}
          {discount > 0 && (
            <span className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full bg-[#FFC107] text-[#111111]">
              -{discount}%
            </span>
          )}
        </div>

        <button
          onClick={() => toggle(product)}
          data-testid={`fav-toggle-${product.id}`}
          className={`absolute top-3 right-3 h-9 w-9 grid place-items-center rounded-full border transition-colors ${
            isFav
              ? "bg-[#009B3A] border-[#009B3A] text-white"
              : "bg-black/50 border-white/20 text-white hover:bg-black/70"
          }`}
          aria-label="Favoritar"
        >
          <Heart size={16} fill={isFav ? "currentColor" : "none"} />
        </button>
      </div>

      <div className="p-4 flex flex-col flex-1">
        {product.brand ? (
          <span className="text-[11px] uppercase tracking-widest text-[#1E3A8A] font-semibold mb-1">
            {product.brand.replace(/-/g, " ")}
          </span>
        ) : (
          <span className="text-[11px] uppercase tracking-widest text-gray-500 font-semibold mb-1">
            {product.group}
          </span>
        )}
        <Link to={`/produto/${product.slug}`} className="flex-1">
          <h3 className="text-sm font-medium text-white leading-snug line-clamp-2 hover:text-[#FFC107] transition-colors">
            {product.name}
          </h3>
        </Link>

        {product.reviews_count > 0 && (
          <div className="flex items-center gap-1 mt-2 text-[#FFC107]">
            <Star size={13} fill="currentColor" />
            <span className="text-xs text-gray-400">
              {product.rating} ({product.reviews_count})
            </span>
          </div>
        )}

        <div className="mt-3 flex items-end justify-between gap-2">
          <div>
            {discount > 0 && (
              <span className="block text-xs text-gray-500 line-through">
                {formatBRL(product.compare_at_price)}
              </span>
            )}
            <span className="text-lg font-display font-bold text-white">
              {formatBRL(product.price)}
            </span>
          </div>
          <button
            onClick={() => addItem(product)}
            data-testid={`add-cart-${product.id}`}
            disabled={product.stock <= 0}
            className="bg-[#1E3A8A] text-white text-xs font-semibold rounded-full px-4 py-2 hover:bg-[#152b66] transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {product.stock <= 0 ? "Esgotado" : "Comprar"}
          </button>
        </div>
      </div>
    </motion.div>
  );
}
