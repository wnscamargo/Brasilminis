import { useEffect } from "react";
import { useSiteContent } from "@/lib/siteContent";
import MarkdownContent from "@/components/MarkdownContent";

// Página institucional genérica (Sobre, Trocas, Frete) — conteúdo 100% do Admin.
export default function InstitutionalPage({ pageKey }) {
  const { pages, loading } = useSiteContent();
  const page = pages[pageKey];

  useEffect(() => {
    if (page) {
      document.title = page.seo_title || page.title || "Brasil Minis";
      if (page.seo_description) {
        let m = document.querySelector('meta[name="description"]');
        if (!m) { m = document.createElement("meta"); m.name = "description"; document.head.appendChild(m); }
        m.content = page.seo_description;
      }
    }
    return () => { document.title = "Brasil Minis"; };
  }, [page]);

  if (loading) {
    return <div className="max-w-[900px] mx-auto px-4 lg:px-8 py-16"><div className="h-10 w-64 bg-white/10 rounded animate-pulse mb-6" /><div className="space-y-3">{Array.from({length:5}).map((_,i)=><div key={i} className="h-4 bg-white/5 rounded animate-pulse" />)}</div></div>;
  }

  if (!page) {
    return <div className="max-w-[900px] mx-auto px-4 lg:px-8 py-24 text-center"><p className="text-gray-400">Esta página não está disponível no momento.</p></div>;
  }

  return (
    <div className="max-w-[900px] mx-auto px-4 lg:px-8 py-12" data-testid={`institutional-${pageKey}`}>
      <div className="bm-stripe rounded-full max-w-[120px] mb-5" />
      <h1 className="text-3xl lg:text-5xl font-display font-black uppercase text-white" data-testid="institutional-title">{page.title}</h1>
      {page.subtitle && <p className="text-gray-500 mt-2 mb-8 text-lg">{page.subtitle}</p>}
      <article className="bm-card p-6 lg:p-10 mt-4">
        <MarkdownContent>{page.content}</MarkdownContent>
      </article>
    </div>
  );
}
