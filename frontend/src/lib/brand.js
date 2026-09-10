export const BRAND = {
  primary: "#1E3A8A",
  green: "#009B3A",
  yellow: "#FFC107",
  black: "#111111",
  darkGray: "#1F1F1F",
  medGray: "#2E2E2E",
};

// Logo oficial Brasil Minis (PNG com fundo transparente, servido de /public).
export const LOGO_HEADER = "/brasil-minis-logo.png";
export const LOGO_EMBLEM = "/brasil-minis-logo.png";

export const MENU = [
  { label: "Início", to: "/" },
  { label: "Miniaturas", to: "/grupo/miniaturas" },
  { label: "Colecionáveis", to: "/grupo/colecionaveis" },
  { label: "Acessórios", to: "/grupo/acessorios" },
  { label: "Vestuário", to: "/grupo/vestuario" },
  { label: "Presentes", to: "/grupo/presentes" },
  { label: "Lançamentos", to: "/produtos?badge=LANÇAMENTO" },
  { label: "Promoções", to: "/produtos?on_sale=true" },
  { label: "Marcas", to: "/marcas" },
  { label: "Contato", to: "/contato" },
];

export const GROUP_LABELS = {
  miniaturas: "Miniaturas",
  colecionaveis: "Colecionáveis",
  acessorios: "Acessórios",
  vestuario: "Vestuário",
  presentes: "Presentes",
};

export function badgeClass(badge) {
  const map = {
    NOVO: "bg-[#1E3A8A] text-white",
    LANÇAMENTO: "bg-[#009B3A] text-white",
    PROMOÇÃO: "bg-[#FFC107] text-[#111111]",
    "TREASURE HUNT": "bg-gradient-to-r from-green-400 to-emerald-600 text-white",
    "SUPER TH":
      "bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-[0_0_10px_rgba(168,85,247,0.5)]",
    PREMIUM: "bg-[#FFC107]/15 text-[#FFC107] border border-[#FFC107]/30",
    "EDIÇÃO LIMITADA": "bg-[#2E2E2E] text-white border border-white/20",
    "PRÉ-VENDA": "bg-[#2E2E2E] text-white border border-white/20",
    "FRETE GRÁTIS": "bg-[#009B3A]/20 text-[#009B3A] border border-[#009B3A]/30",
  };
  return map[badge] || "bg-[#2E2E2E] text-white";
}

export function formatBRL(value) {
  return (value || 0).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}
