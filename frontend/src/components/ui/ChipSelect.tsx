// Фільтр-чип з випадним списком: «+ Менеджер» → галочки з пошуком; активний — синій «Менеджер: Олена, Андрій ×».
import { useMemo, useRef, useState, type ReactNode } from "react";
import { Check } from "lucide-react";
import { FilterChip } from "./nav";
import { useOutside } from "./hooks";

export type ChipOption = { value: string; label: string; color?: string; icon?: ReactNode };

export function ChipSelect({ label, options, value, onChange, single = false, search = true }: {
  label: string; options: ChipOption[]; value: string[]; onChange: (v: string[]) => void; single?: boolean; search?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [hl, setHl] = useState(0);
  const box = useRef<HTMLSpanElement>(null);
  useOutside(box, () => setOpen(false), open);
  const shown = useMemo(() => {
    const s = q.trim().toLowerCase();
    return s ? options.filter((o) => o.label.toLowerCase().includes(s)) : options;
  }, [options, q]);
  const names = value.map((v) => options.find((o) => o.value === v)?.label ?? v);
  const shownValue = names.length ? `${label}: ${names.length > 2 ? `${names.slice(0, 2).join(", ")} +${names.length - 2}` : names.join(", ")}` : undefined;
  const toggle = (v: string) => {
    if (single) { onChange(value[0] === v ? [] : [v]); setOpen(false); return; }
    onChange(value.includes(v) ? value.filter((x) => x !== v) : [...value, v]);
  };
  return (
    <span className="chip-sel" ref={box}>
      <FilterChip label={label} value={shownValue} onClick={() => { setOpen((o) => !o); setQ(""); setHl(0); }} onClear={() => onChange([])} />
      {open && (
        <div className="pop chip-pop" role="listbox" aria-multiselectable={!single} aria-label={label}>
          {search && options.length > 7 && (
            <input autoFocus className="chip-search" value={q} placeholder="Пошук…" onChange={(e) => { setQ(e.target.value); setHl(0); }}
              onKeyDown={(e) => {
                if (e.key === "ArrowDown") { e.preventDefault(); setHl((h) => Math.min(h + 1, shown.length - 1)); }
                else if (e.key === "ArrowUp") { e.preventDefault(); setHl((h) => Math.max(h - 1, 0)); }
                else if (e.key === "Enter" && shown[hl]) { e.preventDefault(); toggle(shown[hl].value); }
              }} />
          )}
          <div className="chip-list">
            {shown.map((o, i) => {
              const on = value.includes(o.value);
              return (
                <button key={o.value} type="button" role="option" aria-selected={on} className={`pop-item${i === hl ? " hl" : ""}${on ? " on" : ""}`}
                  onMouseEnter={() => setHl(i)} onClick={() => toggle(o.value)}>
                  {!single && <span className={`chip-box${on ? " on" : ""}`} aria-hidden>{on && <Check size={11} strokeWidth={3} />}</span>}
                  {o.color && <span className="chip-dot" style={{ background: o.color }} />}
                  {o.icon}
                  <span className="ell" style={{ flex: 1 }}>{o.label}</span>
                  {single && on && <Check size={14} />}
                </button>
              );
            })}
            {!shown.length && <div className="note-empty">Нічого не знайдено</div>}
          </div>
          {!single && value.length > 0 && (
            <div className="chip-foot"><span>Вибрано {value.length}</span><button type="button" className="btn quiet sm" onClick={() => onChange([])}>Скинути</button></div>
          )}
        </div>
      )}
    </span>
  );
}
