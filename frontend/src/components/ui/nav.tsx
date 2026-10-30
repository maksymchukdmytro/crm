// Вкладки-пігулки з лічильниками й «Ще», сегмент, фільтр-чип, статус-пігулка, позначка.
import { useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { Check, ChevronDown, Plus, X } from "lucide-react";
import type { Status } from "../../lib/types";
import { useOutside } from "./hooks";

// ---------------------------------------------------------------- статус і позначки
export function StatusPill({ status, color, name, current = false, size }: {
  status?: Pick<Status, "name" | "color"> | null; color?: string; name?: string; current?: boolean; size?: "lg";
}) {
  const c = status?.color ?? color;
  const n = status?.name ?? name;
  if (!n) return null;
  return (
    <span className={`pill${current ? " cur" : ""}${size ? ` ${size}` : ""}`} title={n} style={{ ["--c" as string]: c }}>
      {current && <Check size={13} strokeWidth={2.4} aria-hidden style={{ marginLeft: -2 }} />}
      <span className="ell">{n}</span>
    </span>
  );
}

export function Tag({ kind = "", children, title, icon }: { kind?: "" | "ok" | "warn" | "bad" | "info"; children: ReactNode; title?: string; icon?: ReactNode }) {
  return <span className={`badge ${kind}`} title={title}>{icon}{children}</span>;
}

// ---------------------------------------------------------------- вкладки
export type TabItem<K extends string = string> = { key: K; label: ReactNode; count?: number | null; hot?: boolean; title?: string; color?: string };

/** Вкладки, що не вмістились у ширину, ховаються в «Ще ▾» (активна завжди лишається видимою). */
export function Tabs<K extends string>({ items, value, onChange, className = "", label = "Вкладки" }: {
  items: TabItem<K>[]; value: K; onChange: (k: K) => void; className?: string; label?: string;
}) {
  const wrap = useRef<HTMLDivElement>(null);
  const measure = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(items.length);
  const [open, setOpen] = useState(false);
  const more = useRef<HTMLDivElement>(null);
  useOutside(more, () => setOpen(false), open);

  useLayoutEffect(() => {
    const el = wrap.current, m = measure.current;
    if (!el || !m) return;
    const calc = () => {
      const avail = el.clientWidth;
      const widths = Array.from(m.children).map((c) => (c as HTMLElement).offsetWidth + 2);
      const moreW = 70;
      let sum = 0, n = 0;
      for (let i = 0; i < widths.length; i++) {
        const rest = i < widths.length - 1 ? moreW : 0;
        if (sum + widths[i] + rest > avail) break;
        sum += widths[i]; n++;
      }
      setVisible(n === widths.length ? n : Math.max(1, n));
    };
    calc();
    const ro = new ResizeObserver(calc);
    ro.observe(el);
    return () => ro.disconnect();
  }, [items]);

  const activeIdx = items.findIndex((i) => i.key === value);
  let shown = items.slice(0, visible);
  let hidden = items.slice(visible);
  if (activeIdx >= visible && visible > 0) {                     // активну вкладку не ховаємо
    shown = [...items.slice(0, visible - 1), items[activeIdx]];
    hidden = items.filter((_, i) => i >= visible - 1 && i !== activeIdx);
  }
  const tab = (t: TabItem<K>) => (
    <button key={t.key} role="tab" aria-selected={t.key === value} className={`${t.key === value ? "on" : ""}${t.color ? " tinted" : ""}`} title={t.title}
      style={t.color ? ({ "--c": t.color } as CSSProperties) : undefined}
      onClick={() => onChange(t.key)}>
      {t.label}
      {t.count != null && <span className={`n${t.hot && t.count ? " hot" : ""}`}>{t.count}</span>}
    </button>
  );
  return (
    <div className={`tabs-wrap ${className}`} ref={wrap}>
      <div className="tabs" role="tablist" aria-label={label}>
        {shown.map(tab)}
        {hidden.length > 0 && (
          <div className="tabs-more" ref={more}>
            <button aria-haspopup="menu" aria-expanded={open} onClick={() => setOpen((o) => !o)}>Ще <ChevronDown size={14} /></button>
            {open && (
              <div className="pop tabs-pop" role="menu">
                {hidden.map((t) => (
                  <button key={t.key} role="menuitem" className="pop-item" onClick={() => { onChange(t.key); setOpen(false); }}>
                    <span className="ell" style={{ flex: 1 }}>{t.label}</span>
                    {t.count != null && <span className="count">{t.count}</span>}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
      <div className="tabs tabs-measure" ref={measure} aria-hidden>
        {items.map((t) => <button key={t.key} tabIndex={-1}>{t.label}{t.count != null && <span className="n">{t.count}</span>}</button>)}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- сегмент
export function Segmented<K extends string>({ items, value, onChange, label }: {
  items: { key: K; label: ReactNode; icon?: ReactNode; title?: string }[]; value: K; onChange: (k: K) => void; label?: string;
}) {
  return (
    <div className="seg" role="radiogroup" aria-label={label}>
      {items.map((i) => (
        <button key={i.key} role="radio" aria-checked={i.key === value} className={i.key === value ? "on" : ""} title={i.title}
          onClick={() => onChange(i.key)}>{i.icon}{i.label}</button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------- фільтр-чип
/** Неактивний — пунктирний «+ Менеджер»; активний — синій «Менеджер: Олена ×». */
export function FilterChip({ label, value, onClick, onClear, icon }: {
  label: string; value?: ReactNode; onClick?: () => void; onClear?: () => void; icon?: ReactNode;
}) {
  const on = value != null && value !== "";
  return (
    <span className={`fchip${on ? " on" : ""}`} role="button" tabIndex={0} onClick={onClick}
      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onClick?.(); } }}>
      {on ? icon : <Plus size={13} aria-hidden />}
      <span className="ell">{on ? value : label}</span>
      {on && onClear && (
        <span className="x" role="button" aria-label={`Скинути: ${label}`} tabIndex={0}
          onClick={(e) => { e.stopPropagation(); onClear(); }}
          onKeyDown={(e) => { if (e.key === "Enter") { e.stopPropagation(); onClear(); } }}><X size={12} /></span>
      )}
    </span>
  );
}
