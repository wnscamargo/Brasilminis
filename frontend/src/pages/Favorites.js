import { Link } from "react-router-dom";
import { Heart } from "lucide-react";
import { useFavorites } from "@/context/FavoritesContext";
import { useAuth } from "@/context/AuthContext";
import ProductCard from "@/components/ProductCard";

export default function Favorites() {
  const { products } = useFavorites();
  const { user } = useAuth();

  if (!user)
    return (
      <div className="max-w-[600px] mx-auto px-4 py-24 text-center">
        <Heart size={48} className="mx-auto text-[#2e2e2e]" />
        <h1 className="text-2xl font-display font-bold text-white mt-6">Entre para ver seus favoritos</h1>
        <Link to="/login" className="inline-block mt-6 bg-[#FFC107] text-[#111111] font-bold uppercase rounded-full px-8 py-3.5">Fazer login</Link>
      </div>
    );

  return (
    <div className="max-w-[1400px] mx-auto px-4 lg:px-8 py-10">
      <h1 className="text-3xl lg:text-4xl font-display font-black uppercase text-white mb-8">Favoritos</h1>
      {products.length === 0 ? (
        <div className="bm-card p-16 text-center text-gray-400">
          Você ainda não favoritou nenhum produto. <Link to="/produtos" className="text-[#FFC107]">Explorar</Link>
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6">
          {products.map((p, i) => (
            <ProductCard key={p.id} product={p} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}
