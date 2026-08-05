import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";

export default function Brands() {
  const [brands, setBrands] = useState([]);
  useEffect(() => {
    api.get("/brands").then((r) => setBrands(r.data));
  }, []);

  return (
    <div className="max-w-[1400px] mx-auto px-4 lg:px-8 py-12">
      <div className="bm-stripe rounded-full max-w-[120px] mb-5" />
      <h1 className="text-3xl lg:text-5xl font-display font-black uppercase text-white">Marcas</h1>
      <p className="text-gray-500 mt-2 mb-10">As melhores fabricantes de miniaturas do mundo, reunidas aqui.</p>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {brands.map((b) => (
          <Link
            key={b.id}
            to={`/produtos?brand=${b.slug}`}
            className="group bm-card p-8 h-40 flex flex-col items-center justify-center text-center hover:border-[#FFC107] transition-colors"
          >
            <span className="text-xl font-display font-black uppercase tracking-tight text-white group-hover:text-[#FFC107] transition-colors">
              {b.name}
            </span>
            <span className="text-xs text-gray-500 mt-2">Ver produtos</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
