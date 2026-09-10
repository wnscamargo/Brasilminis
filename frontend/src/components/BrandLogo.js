import { useSiteConfig } from "@/context/SiteConfigContext";

// Limites de altura por contexto para nunca quebrar header/nav (proporção preservada).
const MAX_HEIGHT = {
  header: "clamp(40px, 8vw, 72px)",
  footer: "80px",
  auth: "120px",
  admin: "44px",
  hero: "200px",
};
const MAX_WVW = { header: "55vw", footer: "70vw", auth: "80vw", admin: "60vw", hero: "80vw" };

export default function BrandLogo({ variant = "header", className = "", alt = "Brasil Minis - Miniaturas e Diecast", widthOverride }) {
  const { logoSrc, logo_width } = useSiteConfig();
  const w = widthOverride || logo_width || 200;
  return (
    <img
      src={logoSrc}
      alt={alt}
      loading="eager"
      decoding="async"
      data-testid="brand-logo"
      className={`object-contain ${className}`}
      style={{
        width: "auto",
        height: "auto",
        maxWidth: `min(${w}px, ${MAX_WVW[variant] || "80vw"})`,
        maxHeight: MAX_HEIGHT[variant] || "72px",
      }}
    />
  );
}
