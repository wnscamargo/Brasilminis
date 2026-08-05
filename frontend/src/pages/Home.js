import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Flame, Sparkles, Tag } from "lucide-react";
import api from "@/lib/api";
import { GROUP_LABELS } from "@/lib/brand";
import ProductCard from "@/components/ProductCard";
import TrustIcons from "@/components/TrustIcons";

const HERO_IMG =
  "https://images.unsplash.com/photo-1637494873826-795116ba38cc?crop=entropy&cs=srgb&fm=jpg&q=85&w=1600";

export default function Home() {
  const [banner, setBanner] = useState(null);
  const [featured, setFeatured] = useState([]);
  const [launches, setLaunches] = useState([]);
  const [sale, setSale] = useState([]);
  const [brands, setBrands] = useState([]);

  useEffect(() => {
    (async () => {
      try {
        const [b, f, l, s, br] = await Promise.all([
          api.get("/banners"),
          api.get("/products?featured=true&limit=8"),
          api.get("/products?badge=LANÇAMENTO&limit=4"),
          api.get("/products?on_sale=true&limit=4"),
          api.get("/brands"),
        ]);
        setBanner(b.data[0]);
        setFeatured(f.data.items);
        setLaunches(l.data.items);
        setSale(s.data.items);
        setBrands(br.data);
      } catch {}
    })();
  }, []);

  return (
    <div>
      {/* HERO */}
      <section className="relative min-h-[88vh] flex items-center overflow-hidden">
        <img src={banner?.image || HERO_IMG} alt="Garagem premium" className="absolute inset-0 h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-r from-[#111111] via-[#111111]/85 to-[#111111]/30" />
        <div className="absolute inset-0 bg-[#111111]/30" />
        <div className="relative max-w-[1400px] mx-auto px-4 lg:px-8 w-full">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="max-w-2xl"
          >
            <span className="inline-flex items-center gap-2 text-[#FFC107] text-xs uppercase tracking-[0.3em] font-semibold mb-5">
              <span className="h-px w-8 bg-[#FFC107]" /> Brasil Minis
            </span>
            <h1 className="text-5xl lg:text-7xl font-display font-black uppercase tracking-tighter text-white leading-[0.95]">
              {banner?.title || "Sua paixão em miniatura."}
            </h1>
            <p className="mt-6 text-lg lg:text-xl text-gray-300 max-w-lg">
              {banner?.subtitle || "As melhores marcas e edições exclusivas estão aqui."}
            </p>
            <div className="mt-9 flex flex-wrap gap-4">
              <Link
                to="/produtos"
                data-testid="hero-comprar"
                className="bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full px-8 py-4 hover:bg-[#e0a800] transition-colors shadow-[0_0_25px_rgba(255,193,7,0.35)] flex items-center gap-2"
              >
                Comprar Agora <ArrowRight size={18} />
              </Link>
              <Link
                to="/produtos?badge=LANÇAMENTO"
                data-testid="hero-lancamentos"
                className="border border-white/30 text-white font-semibold uppercase tracking-wider rounded-full px-8 py-4 hover:bg-white/10 transition-colors"
              >
                Ver Lançamentos
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      <TrustIcons />

      {/* Categories groups */}
      <section className="max-w-[1400px] mx-auto px-4 lg:px-8 py-20">
        <SectionTitle icon={Sparkles} kicker="Explore" title="Categorias" />
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-8">
          {Object.entries(GROUP_LABELS).map(([slug, label], i) => (
            <motion.div
              key={slug}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05 }}
            >
              <Link
                to={`/grupo/${slug}`}
                data-testid={`group-card-${slug}`}
                className="group block bm-card p-6 h-32 flex flex-col justify-between hover:border-[#FFC107] transition-colors"
              >
                <span className="text-3xl font-display font-black text-[#2e2e2e] group-hover:text-[#1E3A8A] transition-colors">
                  0{i + 1}
                </span>
                <span className="text-sm font-semibold uppercase tracking-wide text-white">
                  {label}
                </span>
              </Link>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Featured / Mais vendidos */}
      <section className="max-w-[1400px] mx-auto px-4 lg:px-8 pb-8">
        <SectionTitle icon={Flame} kicker="Destaques" title="Mais Vendidos" link="/produtos" />
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mt-8">
          {featured.map((p, i) => (
            <ProductCard key={p.id} product={p} index={i} />
          ))}
        </div>
      </section>

      {/* Launches band */}
      {launches.length > 0 && (
        <section className="max-w-[1400px] mx-auto px-4 lg:px-8 py-16">
          <SectionTitle icon={Sparkles} kicker="Novidades" title="Lançamentos" link="/produtos?badge=LANÇAMENTO" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mt-8">
            {launches.map((p, i) => (
              <ProductCard key={p.id} product={p} index={i} />
            ))}
          </div>
        </section>
      )}

      {/* Promo banner */}
      <section className="max-w-[1400px] mx-auto px-4 lg:px-8 py-4">
        <div className="relative overflow-hidden rounded-3xl bm-carbon border border-[#2e2e2e] p-10 lg:p-16">
          <div className="bm-stripe absolute top-0 left-0" />
          <div className="max-w-xl">
            <span className="text-[#009B3A] uppercase tracking-[0.3em] text-xs font-bold">Frete Grátis</span>
            <h3 className="text-3xl lg:text-4xl font-display font-black uppercase text-white mt-3 leading-tight">
              Acima de R$300 o frete é por nossa conta
            </h3>
            <p className="text-gray-400 mt-3">Monte sua coleção e economize. Válido para todo o Brasil.</p>
            <Link
              to="/produtos"
              className="inline-flex items-center gap-2 mt-6 bg-[#FFC107] text-[#111111] font-bold uppercase tracking-wider rounded-full px-7 py-3.5 hover:bg-[#e0a800] transition-colors"
            >
              Aproveitar <ArrowRight size={18} />
            </Link>
          </div>
        </div>
      </section>

      {/* Promotions */}
      {sale.length > 0 && (
        <section className="max-w-[1400px] mx-auto px-4 lg:px-8 py-16">
          <SectionTitle icon={Tag} kicker="Ofertas" title="Promoções" link="/produtos?on_sale=true" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mt-8">
            {sale.map((p, i) => (
              <ProductCard key={p.id} product={p} index={i} />
            ))}
          </div>
        </section>
      )}

      {/* Brands */}
      <section className="max-w-[1400px] mx-auto px-4 lg:px-8 py-12">
        <SectionTitle kicker="Parceiros" title="Marcas" link="/marcas" />
        <div className="flex flex-wrap gap-3 mt-8">
          {brands.map((b) => (
            <Link
              key={b.id}
              to={`/produtos?brand=${b.slug}`}
              className="px-6 py-3 bm-card hover:border-[#1E3A8A] transition-colors text-sm font-display font-semibold uppercase tracking-wider text-gray-200"
            >
              {b.name}
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

function SectionTitle({ icon: Icon, kicker, title, link }) {
  return (
    <div className="flex items-end justify-between gap-4">
      <div>
        {kicker && (
          <span className="flex items-center gap-2 text-[#FFC107] text-xs uppercase tracking-[0.3em] font-semibold mb-2">
            {Icon && <Icon size={15} />} {kicker}
          </span>
        )}
        <h2 className="text-3xl lg:text-4xl font-display font-black uppercase tracking-tight text-white">
          {title}
        </h2>
      </div>
      {link && (
        <Link to={link} className="text-sm text-gray-400 hover:text-[#FFC107] flex items-center gap-1 transition-colors whitespace-nowrap">
          Ver tudo <ArrowRight size={15} />
        </Link>
      )}
    </div>
  );
}
