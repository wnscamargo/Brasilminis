import { Instagram, Facebook, Youtube, Send, MessageCircle, Twitter, Music2, Pin } from "lucide-react";

// Mapa plataforma → ícone/label. TikTok usa Music2, Pinterest usa Pin (lucide não tem oficiais).
const META = {
  instagram: { Icon: Instagram, label: "Instagram" },
  facebook: { Icon: Facebook, label: "Facebook" },
  tiktok: { Icon: Music2, label: "TikTok" },
  youtube: { Icon: Youtube, label: "YouTube" },
  whatsapp: { Icon: MessageCircle, label: "WhatsApp" },
  telegram: { Icon: Send, label: "Telegram" },
  twitter: { Icon: Twitter, label: "X / Twitter" },
  pinterest: { Icon: Pin, label: "Pinterest" },
};

const ORDER = ["instagram", "facebook", "tiktok", "youtube", "whatsapp", "telegram", "twitter", "pinterest"];

// `social` = { plataforma: url } (somente ativas com URL, vindas do Admin).
export default function SocialLinks({ social = {}, size = 18, className = "" }) {
  const items = ORDER.filter((k) => social[k]);
  if (items.length === 0) return null;
  return (
    <div className={`flex flex-wrap gap-3 ${className}`} data-testid="social-links">
      {items.map((k) => {
        const { Icon, label } = META[k];
        return (
          <a
            key={k}
            href={social[k]}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={label}
            title={label}
            data-testid={`social-${k}`}
            className="h-10 w-10 grid place-items-center rounded-full border border-[#2e2e2e] text-gray-300 hover:border-[#FFC107] hover:text-[#FFC107] transition-colors"
          >
            <Icon size={size} />
          </a>
        );
      })}
    </div>
  );
}
