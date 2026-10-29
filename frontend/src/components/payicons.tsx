// Значки видів оплат — кольорові плитки, як сітка значків у LP-CRM.
// Ключ значка зберігається у виді оплати (icon), тож нові види можуть брати будь-який із цих.
import type { LucideIcon } from "lucide-react";
import {
  BadgeCheck, Banknote, Calculator, CircleDollarSign, CreditCard, HandCoins, Landmark, Mail, RefreshCw, Smartphone, Undo2,
} from "lucide-react";

type Def = { label: string; color: string; Icon?: LucideIcon; text?: string };

export const PAY_ICONS: Record<string, Def> = {
  cod: { label: "Післяплата", color: "#64748b", Icon: Mail },
  prepay: { label: "Передоплата", color: "#16a34a", Icon: HandCoins },
  prepay_card: { label: "Передоплата на картку", color: "#2563eb", Icon: CreditCard },
  prepay_ok: { label: "Передоплата отримана", color: "#15803d", Icon: BadgeCheck },
  paid: { label: "Оплачено", color: "#16a34a", Icon: CircleDollarSign },
  online: { label: "Онлайн", color: "#7c3aed", Icon: Smartphone },
  card: { label: "Картка", color: "#2563eb", Icon: CreditCard },
  cash: { label: "Готівка", color: "#15803d", Icon: Banknote },
  exchange: { label: "Обмін", color: "#d97706", Icon: RefreshCw },
  refund: { label: "Повернення", color: "#dc2626", Icon: Undo2 },
  pos: { label: "POS-термінал", color: "#475569", Icon: Calculator },
  bank: { label: "Банк", color: "#64748b", Icon: Landmark },
  prom: { label: "Prom", color: "#7c3aed", text: "п/о" },
  olx: { label: "OLX", color: "#0f766e", text: "OLX" },
  rozetkapay: { label: "RozetkaPay", color: "#00a046", text: "RP" },
  rozetka: { label: "Rozetka", color: "#00a046", text: "R" },
  novapay: { label: "NovaPay", color: "#c026d3", text: "NP" },
  ukrposhta: { label: "Укрпошта", color: "#d4a106", text: "УП" },
  meest: { label: "Meest", color: "#e30613", text: "M" },
};

export function PayIcon({ icon, size = 22, title }: { icon?: string; size?: number; title?: string }) {
  const d = PAY_ICONS[icon || ""] ?? PAY_ICONS.cash;
  const style = { width: size, height: size, ["--pc" as string]: d.color, fontSize: Math.round(size * 0.42) };
  return (
    <span className="pay-ic" style={style} title={title ?? d.label} aria-hidden={!title}>
      {d.Icon ? <d.Icon size={Math.round(size * 0.6)} strokeWidth={2} /> : d.text}
    </span>
  );
}

/** Код країни → значок-прапорець (емодзі; у Windows показується як дві літери — теж зрозуміло). */
export function flag(code: string) {
  const c = (code || "UA").toUpperCase();
  return String.fromCodePoint(...[...c].map((ch) => 127397 + ch.charCodeAt(0)));
}
