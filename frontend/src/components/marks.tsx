// Позначки замовлень — значок + підпис, як у LP-CRM («Терміново» — червоний знак оклику, «Очікує» — жовтий годинник…).
// Ключ значка зберігається в позначці (icon), колір — у color; список ключів — тут.
import { useEffect, useRef, useState, type ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import {
  Camera, Check, ChevronDown, CircleAlert, Clock3, Eye, FileText, Gift, Handshake, Mail, MessageCircle, Music, Package,
  Pencil, Percent, PhoneCall, PhoneMissed, PhoneOff, Printer, QrCode, Receipt, ScanBarcode, Send, ShoppingBag,
  Star, Store, Tag, Trash2, Truck, Undo2, X, RadioTower,
} from "lucide-react";

export const MARK_ICONS: Record<string, { Icon: LucideIcon; label: string }> = {
  alert: { Icon: CircleAlert, label: "Знак оклику" }, clock: { Icon: Clock3, label: "Годинник" }, pencil: { Icon: Pencil, label: "Олівець" },
  eye: { Icon: Eye, label: "Око" }, check: { Icon: Check, label: "Галочка" }, x: { Icon: X, label: "Хрестик" },
  gift: { Icon: Gift, label: "Подарунок" }, file: { Icon: FileText, label: "Документ" }, receipt: { Icon: Receipt, label: "Чек" },
  package: { Icon: Package, label: "Коробка" }, truck: { Icon: Truck, label: "Вантажівка" }, handshake: { Icon: Handshake, label: "Дроп" },
  printer: { Icon: Printer, label: "Принтер" }, mail: { Icon: Mail, label: "Конверт" }, barcode: { Icon: ScanBarcode, label: "Штрихкод" },
  qr: { Icon: QrCode, label: "QR-код" }, "phone-wait": { Icon: PhoneCall, label: "Дзвінок" }, "phone-missed": { Icon: PhoneMissed, label: "Недодзвон" },
  signal: { Icon: RadioTower, label: "Сигнал" }, "phone-off": { Icon: PhoneOff, label: "Відмова" }, percent: { Icon: Percent, label: "Знижка" },
  trash: { Icon: Trash2, label: "Кошик" }, undo: { Icon: Undo2, label: "Повернення" }, message: { Icon: MessageCircle, label: "Повідомлення" },
  send: { Icon: Send, label: "Літачок" }, music: { Icon: Music, label: "Нота" }, camera: { Icon: Camera, label: "Камера" },
  bag: { Icon: ShoppingBag, label: "Пакет" }, store: { Icon: Store, label: "Магазин" }, tag: { Icon: Tag, label: "Мітка" },
  star: { Icon: Star, label: "Зірка" },
};

export const MARK_COLORS = ["#dc2626", "#ea580c", "#ca8a04", "#16a34a", "#0d9488", "#2563eb", "#7c3aed", "#db2777", "#475569", "#111827"];

type MarkLike = { id: number; name: string; icon?: string | null; color?: string | null };

export function MarkIcon({ icon, color, size = 16 }: { icon?: string | null; color?: string | null; size?: number }) {
  const d = MARK_ICONS[icon || "tag"] ?? MARK_ICONS.tag;
  return <d.Icon size={size} color={color || "#475569"} strokeWidth={2.1} aria-hidden className="mark-ic" />;
}

/** Позначка в рядку списку чи в картці: значок + назва. */
export function MarkBadge({ mark, short = false }: { mark: MarkLike; short?: boolean }) {
  return (
    <span className="mark-badge" title={mark.name} style={{ ["--mc" as string]: mark.color || "#475569" }}>
      <MarkIcon icon={mark.icon} color={mark.color} size={13} />{!short && <span>{mark.name}</span>}
    </span>
  );
}

/** Випадний список «значок + підпис» (вид оплати, позначка): видно, що вибрано, і що є на вибір. */
export function IconPick<T extends { id: number; name: string }>({ items, value, onChange, render, placeholder, emptyLabel, ariaLabel, className = "" }: {
  items: T[]; value: number | null | ""; onChange: (id: number | null) => void; render: (x: T) => ReactNode;
  placeholder: ReactNode; emptyLabel?: string; ariaLabel: string; className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [up, setUp] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const cur = items.find((x) => x.id === value);
  const toggle = () => {
    // біля нижнього краю (кнопка «Зберегти» внизу вікна) — відкриваємо список угору
    const r = ref.current?.getBoundingClientRect();
    setUp(!!r && window.innerHeight - r.bottom < 340 && r.top > 340);
    setOpen(!open);
  };
  useEffect(() => {
    if (!open) return;
    const h = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    const k = (e: KeyboardEvent) => { if (e.key === "Escape") { e.stopPropagation(); setOpen(false); } };
    document.addEventListener("mousedown", h);
    document.addEventListener("keydown", k, true);
    return () => { document.removeEventListener("mousedown", h); document.removeEventListener("keydown", k, true); };
  }, [open]);
  return (
    <div className={`ipick ${className}`} ref={ref}>
      <button type="button" className={`ipick-btn ${cur ? "" : "empty"}`} aria-haspopup="listbox" aria-expanded={open} aria-label={ariaLabel} onClick={toggle}>
        {cur ? render(cur) : placeholder}<ChevronDown size={15} className="ipick-ch" />
      </button>
      {open && (
        <div className={`ipick-list ${up ? "up" : ""}`} role="listbox" aria-label={ariaLabel}>
          {emptyLabel && <button type="button" role="option" aria-selected={!cur} className={!cur ? "on" : ""} onClick={() => { onChange(null); setOpen(false); }}><span className="muted">{emptyLabel}</span></button>}
          {items.map((x) => (
            <button type="button" role="option" key={x.id} aria-selected={x.id === value} className={x.id === value ? "on" : ""}
              onClick={() => { onChange(x.id); setOpen(false); }}>{render(x)}</button>
          ))}
        </div>
      )}
    </div>
  );
}

/** Налаштування позначки: значок і колір (кнопка-значок → сітка значків і кольорів). */
export function MarkLookPick({ icon, color, onChange }: { icon?: string | null; color?: string | null; onChange: (icon: string, color: string) => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const ic = icon || "tag", co = color || "#475569";
  useEffect(() => {
    if (!open) return;
    const h = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, [open]);
  return (
    <div className="mlook" ref={ref}>
      <button type="button" className="mlook-btn" title="Значок і колір позначки" aria-label="Значок і колір позначки" onClick={() => setOpen(!open)}>
        <MarkIcon icon={ic} color={co} size={18} />
      </button>
      {open && (
        <div className="mlook-pop">
          <div className="mlook-icons">{Object.entries(MARK_ICONS).map(([k, d]) => (
            <button type="button" key={k} title={d.label} aria-label={d.label} className={k === ic ? "on" : ""} onClick={() => onChange(k, co)}>
              <d.Icon size={17} color={co} /></button>
          ))}</div>
          <div className="mlook-colors">{MARK_COLORS.map((c) => (
            <button type="button" key={c} aria-label={`Колір ${c}`} className={c === co ? "on" : ""} style={{ background: c }} onClick={() => onChange(ic, c)} />
          ))}</div>
        </div>
      )}
    </div>
  );
}
