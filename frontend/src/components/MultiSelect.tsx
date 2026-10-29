// Випадний список з галочками й пошуком (фільтри статистики, фільтри колонок списку замовлень).
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Check, ChevronDown, X } from "lucide-react";

export const EMPTY = "__empty__";

export type MsOption = { value: string; label: string; color?: string; hint?: string | number; depth?: number };

export default function MultiSelect({
  options, value, onChange, placeholder, label, icon, allowEmpty = false, single = false, className = "",
}: {
  options: MsOption[];
  value: string[];
  onChange: (v: string[]) => void;
  placeholder: string;
  label?: string;
  icon?: ReactNode;
  allowEmpty?: boolean;
  single?: boolean;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [hl, setHl] = useState(0);
  const box = useRef<HTMLDivElement>(null);
  const search = useRef<HTMLInputElement>(null);

  const all = useMemo<MsOption[]>(
    () => (allowEmpty ? [{ value: EMPTY, label: "Пусте поле" }, ...options] : options),
    [options, allowEmpty],
  );
  const shown = useMemo(() => {
    const s = q.trim().toLowerCase();
    return s ? all.filter((o) => o.label.toLowerCase().includes(s) || o.value.toLowerCase() === s) : all;
  }, [all, q]);
  const byValue = useMemo(() => new Map(all.map((o) => [o.value, o])), [all]);

  useEffect(() => {
    if (!open) return;
    const h = (e: MouseEvent) => { if (box.current && !box.current.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", h);
    setTimeout(() => search.current?.focus(), 0);
    return () => document.removeEventListener("mousedown", h);
  }, [open]);
  useEffect(() => setHl(0), [q, open]);

  const toggle = (v: string) => {
    if (single) { onChange(value[0] === v ? [] : [v]); setOpen(false); return; }
    onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
  };
  const picked = value.map((v) => byValue.get(v)?.label ?? v);
  const text = !value.length ? placeholder : value.length <= 2 ? picked.join(", ") : `${picked[0]} і ще ${value.length - 1}`;

  return (
    <div className={`ms ${value.length ? "on" : ""} ${open ? "open" : ""} ${className}`} ref={box}>
      <button type="button" className="ms-btn" onClick={() => setOpen((o) => !o)} title={label ? `${label}: ${picked.join(", ") || placeholder}` : undefined}
        onKeyDown={(e) => { if (e.key === "ArrowDown" && !open) { e.preventDefault(); setOpen(true); } }}>
        {icon && <span className="ms-ico">{icon}</span>}
        <span className="ms-text">{label && value.length > 0 && <span className="ms-lbl">{label}: </span>}{text}</span>
        {value.length > 0
          ? <span className="ms-x" role="button" aria-label="Скинути" onClick={(e) => { e.stopPropagation(); onChange([]); }}><X size={13} /></span>
          : <ChevronDown size={14} className="ms-chev" />}
      </button>
      {open && (
        <div className="ms-pop" role="listbox" aria-multiselectable={!single}>
          {all.length > 7 && (
            <input ref={search} className="ms-search" value={q} placeholder="Пошук…" onChange={(e) => setQ(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "ArrowDown") { e.preventDefault(); setHl((h) => Math.min(h + 1, shown.length - 1)); }
                else if (e.key === "ArrowUp") { e.preventDefault(); setHl((h) => Math.max(h - 1, 0)); }
                else if (e.key === "Enter") { e.preventDefault(); if (shown[hl]) toggle(shown[hl].value); }
                else if (e.key === "Escape") { e.preventDefault(); setOpen(false); }
              }} />
          )}
          <div className="ms-list">
            {shown.map((o, i) => {
              const on = value.includes(o.value);
              return (
                <div key={o.value} role="option" aria-selected={on} className={`ms-opt ${on ? "on" : ""} ${i === hl ? "hl" : ""} ${o.value === EMPTY ? "empty" : ""}`}
                  style={o.depth ? { paddingLeft: 10 + o.depth * 14 } : undefined}
                  onMouseEnter={() => setHl(i)} onMouseDown={(e) => { e.preventDefault(); toggle(o.value); }}>
                  <span className="ms-box">{on && <Check size={12} strokeWidth={3} />}</span>
                  {o.color && <span className="ms-dot" style={{ background: o.color }} />}
                  <span className="ms-name">{o.label}</span>
                  {o.hint !== undefined && <span className="ms-hint">{o.hint}</span>}
                </div>
              );
            })}
            {!shown.length && <div className="ms-none">Нічого не знайдено</div>}
          </div>
          {!single && value.length > 0 && (
            <div className="ms-foot"><span>Вибрано: {value.length}</span><button type="button" className="btn sm ghost" onClick={() => onChange([])}>Скинути</button></div>
          )}
        </div>
      )}
    </div>
  );
}
