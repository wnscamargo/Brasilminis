import { ShieldCheck, Truck, BadgeCheck, Users, Headphones } from "lucide-react";

const ITEMS = [
  { icon: ShieldCheck, label: "Compra Segura" },
  { icon: Truck, label: "Entrega Nacional" },
  { icon: BadgeCheck, label: "Produtos Originais" },
  { icon: Users, label: "Feito p/ Colecionadores" },
  { icon: Headphones, label: "Atendimento Especializado" },
];

export default function TrustIcons() {
  return (
    <section className="border-y border-[#2e2e2e] bm-honeycomb">
      <div className="max-w-[1400px] mx-auto px-4 lg:px-8 py-8 grid grid-cols-2 md:grid-cols-5 gap-6">
        {ITEMS.map(({ icon: Icon, label }) => (
          <div key={label} className="flex flex-col md:flex-row items-center gap-3 text-center md:text-left">
            <div className="h-11 w-11 shrink-0 grid place-items-center rounded-full border border-[#2e2e2e] text-[#FFC107]">
              <Icon size={22} strokeWidth={1.6} />
            </div>
            <span className="text-xs md:text-sm text-gray-300 font-medium">{label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
