// Значки видів оплат — за змістом, як у LP-CRM: кольорова картинка без плитки + підпис поруч.
// Загальні види — зрозумілі картинки (конверт із грошима — післяплата, купюра з рукою — передоплата…);
// сервіси (Rozetka, NovaPay, Укрпошта…) — кружечок у кольорі сервісу з абревіатурою (логотипи брендів не малюємо).
// Синя крапка в куті — «гроші при отриманні» (післяплата), як у LP-CRM.
import type { LucideIcon } from "lucide-react";
import {
  BadgeCheck, Banknote, BanknoteArrowDown, Calculator, CircleDollarSign, CreditCard, HandCoins, Landmark, MailOpen,
  RefreshCw, SmartphoneNfc, WalletCards,
} from "lucide-react";

type Def = { label: string; color: string; Icon?: LucideIcon; text?: string; cod?: boolean };

export const PAY_ICONS: Record<string, Def> = {
  cod: { label: "Післяплата (конверт із грошима)", color: "#475569", Icon: MailOpen, cod: true },
  prepay: { label: "Передоплата (купюра в руці)", color: "#16a34a", Icon: HandCoins },
  prepay_card: { label: "Передоплата на картку", color: "#2563eb", Icon: WalletCards },
  prepay_ok: { label: "Передоплата отримана", color: "#15803d", Icon: BadgeCheck },
  paid: { label: "Оплачено", color: "#16a34a", Icon: CircleDollarSign },
  online: { label: "Онлайн-оплата", color: "#475569", Icon: SmartphoneNfc },
  card: { label: "Картка", color: "#2563eb", Icon: CreditCard },
  cash: { label: "Готівка", color: "#15803d", Icon: Banknote },
  exchange: { label: "Обмін", color: "#d97706", Icon: RefreshCw },
  refund: { label: "Повернення коштів", color: "#dc2626", Icon: BanknoteArrowDown },
  pos: { label: "POS-термінал", color: "#475569", Icon: Calculator },
  bank: { label: "Банк", color: "#475569", Icon: Landmark },
  prom: { label: "Prom", color: "#7c3aed", text: "п/о" },
  olx: { label: "OLX", color: "#0f766e", text: "olx" },
  rozetkapay: { label: "RozetkaPay", color: "#00a046", text: "RP" },
  rozetka: { label: "Rozetka (післяплата)", color: "#00a046", text: "R", cod: true },
  novapay: { label: "NovaPay (післяплата)", color: "#9d2bd6", text: "NP", cod: true },
  ukrposhta: { label: "Укрпошта (післяплата)", color: "#e8a800", text: "УП", cod: true },
  meest: { label: "Meest (післяплата)", color: "#e30613", text: "M", cod: true },
};

export function PayIcon({ icon, size = 22, title }: { icon?: string; size?: number; title?: string }) {
  const d = PAY_ICONS[icon || ""] ?? PAY_ICONS.cash;
  const style = { width: size, height: size, ["--pc" as string]: d.color, fontSize: Math.round(size * (d.text && d.text.length > 2 ? 0.36 : 0.42)) };
  return (
    <span className={`pay-ic ${d.Icon ? "glyph" : "brand"}`} style={style} title={title ?? d.label} aria-hidden={!title}>
      {d.Icon ? <d.Icon size={Math.round(size * 0.92)} strokeWidth={1.9} /> : d.text}
      {d.cod && <i className="pay-cod" aria-hidden />}
    </span>
  );
}

/** Вид оплати: значок + назва (скрізь, де раніше був лише значок). */
export function PayLabel({ icon, name, size = 18 }: { icon?: string; name: string; size?: number }) {
  return <span className="pay-label"><PayIcon icon={icon} size={size} /><span>{name}</span></span>;
}

/** Код країни → значок-прапорець (емодзі; у Windows показується як дві літери — теж зрозуміло). */
export function flag(code: string) {
  const c = (code || "UA").toUpperCase();
  return String.fromCodePoint(...[...c].map((ch) => 127397 + ch.charCodeAt(0)));
}
