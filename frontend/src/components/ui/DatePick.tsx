// Календар CRM (етап A4, docs/UI-NEXT.md) замість системних <input type="date"> і "datetime-local".
// Calendar — місяць сіткою: українські назви, тиждень з понеділка, сьогодні виділено, вихідні сірим, стрілки з клавіатури.
// DateField — одна дата; DateRangeField — період з пресетами (два кліки, проміжок підсвічено); DateTimePicker — дата й час
// (чипи годин і поле свого часу). Поле показує дату по-людськи («3 лист.»), значення — ISO, як і раніше.
// На ПК календар спливає поверх усього (Floating), на телефоні — шторкою (Sheet).
import { useEffect, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, Clock } from "lucide-react";
import { Floating } from "./HoverCard";
import { Sheet } from "./bars";
import { useMobile } from "./hooks";

const MONTHS = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"];
const MON_SHORT = ["січ.", "лют.", "бер.", "квіт.", "трав.", "черв.", "лип.", "серп.", "вер.", "жовт.", "лист.", "груд."];
const WD = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"];

const pad = (n: number) => String(n).padStart(2, "0");
/** Дата → "YYYY-MM-DD" за місцевим часом. */
export const isoDate = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const parse = (s?: string | null) => {
  const m = s ? /^(\d{4})-(\d{2})-(\d{2})/.exec(s) : null;
  return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null;
};
const shift = (s: string, n: number) => { const d = parse(s)!; d.setDate(d.getDate() + n); return isoDate(d); };
const thisYear = () => new Date().getFullYear();

/** «3 лист.», інший рік — «3 лист. 2025». */
export function fmtDate(s?: string | null, withYear?: boolean): string {
  const d = parse(s);
  if (!d) return "";
  const y = withYear ?? d.getFullYear() !== thisYear();
  return `${d.getDate()} ${MON_SHORT[d.getMonth()]}${y ? ` ${d.getFullYear()}` : ""}`;
}

/** «1–7 лист.», «28 жовт. — 3 лист.», «з 3 лист.». */
export function fmtRange(a?: string | null, b?: string | null): string {
  if (!a && !b) return "";
  if (!b) return `з ${fmtDate(a)}`;
  if (!a) return `по ${fmtDate(b)}`;
  if (a === b) return fmtDate(a);
  const A = parse(a)!, B = parse(b)!;
  const yr = A.getFullYear() !== B.getFullYear() || A.getFullYear() !== thisYear();
  if (A.getFullYear() === B.getFullYear() && A.getMonth() === B.getMonth())
    return `${A.getDate()}–${B.getDate()} ${MON_SHORT[B.getMonth()]}${yr ? ` ${B.getFullYear()}` : ""}`;
  return `${fmtDate(a, yr)} — ${fmtDate(b, yr)}`;
}

export type DatePreset = [label: string, from: string, to: string];
/** Типові відрізки: Сьогодні, Учора, 7 днів, 30 днів, Цей місяць, Минулий місяць. */
export function datePresets(now = new Date()): DatePreset[] {
  const t = isoDate(now);
  const y = now.getFullYear(), m = now.getMonth();
  return [
    ["Сьогодні", t, t], ["Учора", shift(t, -1), shift(t, -1)], ["7 днів", shift(t, -6), t], ["30 днів", shift(t, -29), t],
    ["Цей місяць", isoDate(new Date(y, m, 1)), t], ["Минулий місяць", isoDate(new Date(y, m - 1, 1)), isoDate(new Date(y, m, 0))],
  ];
}

// ---------------------------------------------------------------- місяць сіткою
export function Calendar({ value, from, to, min, max, onPick, onHover }: {
  value?: string; from?: string; to?: string; min?: string; max?: string;
  onPick: (iso: string) => void; onHover?: (iso: string | null) => void;
}) {
  const today = isoDate(new Date());
  const start = (value || to || from || (max && max < today ? max : today)).slice(0, 10);
  const [month, setMonth] = useState(() => { const d = parse(start)!; return new Date(d.getFullYear(), d.getMonth(), 1); });
  const [focus, setFocus] = useState(start);
  const grid = useRef<HTMLDivElement>(null);
  const byKey = useRef(false);
  const cells = useMemo(() => {
    const first = new Date(month);
    first.setDate(1 - ((first.getDay() + 6) % 7));
    return Array.from({ length: 42 }, (_, i) => { const d = new Date(first); d.setDate(first.getDate() + i); return d; });
  }, [month]);
  useEffect(() => {
    if (!byKey.current) return;
    byKey.current = false;
    grid.current?.querySelector<HTMLButtonElement>(`[data-d="${focus}"]`)?.focus();
  }, [focus, month]);

  const go = (n: number) => setMonth(new Date(month.getFullYear(), month.getMonth() + n, 1));
  const moveTo = (iso: string) => {
    const d = parse(iso)!;
    byKey.current = true;
    setFocus(iso);
    if (d.getMonth() !== month.getMonth() || d.getFullYear() !== month.getFullYear()) setMonth(new Date(d.getFullYear(), d.getMonth(), 1));
  };
  const onKey = (e: KeyboardEvent) => {
    const step: Record<string, number> = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
    if (e.key in step) { e.preventDefault(); moveTo(shift(focus, step[e.key])); }
    else if (e.key === "PageUp" || e.key === "PageDown") {
      e.preventDefault();
      const d = parse(focus)!; d.setMonth(d.getMonth() + (e.key === "PageUp" ? -1 : 1)); moveTo(isoDate(d));
    }
  };

  const [lo, hi] = from && to ? (from <= to ? [from, to] : [to, from]) : [from || "", from || ""];
  const shown = cells.some((c) => isoDate(c) === focus) ? focus : isoDate(month);
  return (
    <div className="cal">
      <div className="cal-h">
        <button type="button" className="cal-nav" aria-label="Попередній місяць" onClick={() => go(-1)}><ChevronLeft size={16} /></button>
        <b aria-live="polite">{MONTHS[month.getMonth()]} {month.getFullYear()}</b>
        <button type="button" className="cal-nav" aria-label="Наступний місяць" onClick={() => go(1)}><ChevronRight size={16} /></button>
      </div>
      <div className="cal-wd" aria-hidden>{WD.map((w, i) => <span key={w} className={i > 4 ? "we" : ""}>{w}</span>)}</div>
      <div className="cal-grid" ref={grid} role="grid" aria-label={`${MONTHS[month.getMonth()]} ${month.getFullYear()}`} onKeyDown={onKey}
        onMouseLeave={() => onHover?.(null)}>
        {cells.map((c) => {
          const iso = isoDate(c);
          const off = (!!min && iso < min) || (!!max && iso > max);
          const cls = ["cal-d",
            c.getMonth() !== month.getMonth() && "out", [0, 6].includes(c.getDay()) && "we", iso === today && "today",
            (iso === value || (lo && (iso === lo || iso === hi))) && "on",
            lo && hi !== lo && iso > lo && iso < hi && "in", lo && hi !== lo && iso === lo && "rs", lo && hi !== lo && iso === hi && "re",
          ].filter(Boolean).join(" ");
          return (
            <button key={iso} type="button" data-d={iso} className={cls} disabled={off} tabIndex={iso === shown ? 0 : -1}
              aria-label={`${c.getDate()} ${MON_SHORT[c.getMonth()]} ${c.getFullYear()}${iso === today ? ", сьогодні" : ""}`}
              aria-pressed={iso === value || iso === lo || iso === hi}
              onClick={() => { setFocus(iso); onPick(iso); }} onMouseEnter={() => onHover?.(iso)} onFocus={() => setFocus(iso)}>
              {c.getDate()}
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- період: пресети + два кліки в календарі
export function RangePicker({ from, to, onChange, min, max, presets }: {
  from?: string; to?: string; onChange: (from: string, to: string) => void; min?: string; max?: string; presets?: DatePreset[];
}) {
  const [a, setA] = useState(from || "");
  const [b, setB] = useState(to || "");
  const [hover, setHover] = useState<string | null>(null);
  const pr = presets ?? datePresets();
  const cur = pr.find((p) => p[1] === from && p[2] === to)?.[0];
  const picking = !!a && !b;
  const pick = (d: string) => {
    if (!a || b) { setA(d); setB(""); return; }
    const [x, y] = d < a ? [d, a] : [a, d];
    setA(x); setB(y); onChange(x, y);
  };
  return (
    <div className={`dr${pr.length ? "" : " solo"}`}>
      {pr.length > 0 && <div className="dr-pre" role="group" aria-label="Готові відрізки">
        {pr.map(([n, x, y]) => (
          <button key={n} type="button" className={`dr-chip${cur === n ? " on" : ""}`} aria-pressed={cur === n}
            onClick={() => { setA(x); setB(y); onChange(x, y); }}>{n}</button>
        ))}
      </div>}
      <div className="dr-cal">
        <Calendar from={a} to={picking ? hover ?? "" : b} min={min} max={max} onPick={pick} onHover={setHover} />
        <div className="dr-note">{picking ? `${fmtDate(a)} — оберіть кінець періоду` : a && b ? fmtRange(a, b) : "Оберіть початок періоду"}</div>
      </div>
    </div>
  );
}

/** Спливає поруч з кнопкою на ПК, шторкою на телефоні. */
export function DatePop({ anchor, open, onClose, title, width, children }: {
  anchor: HTMLElement | null; open: boolean; onClose: () => void; title: string; width: number; children: ReactNode;
}) {
  const mobile = useMobile();
  if (!open) return null;
  if (mobile) return <Sheet title={title} onClose={onClose}><div className="dpop m">{children}</div></Sheet>;
  return <Floating anchor={anchor} open onClose={onClose} width={width} className="dpop" label={title}>{children}</Floating>;
}

/** Поле періоду: «7 днів» або «1–7 лист.»; клік — пресети й календар. */
export function DateRangeField({ from, to, onChange, min, max, presets, label = "Період", placeholder = "Період", clearable, className = "" }: {
  from?: string; to?: string; onChange: (from: string, to: string) => void; min?: string; max?: string; presets?: DatePreset[];
  label?: string; placeholder?: string; clearable?: boolean; className?: string;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const pr = presets ?? datePresets();
  const text = pr.find((p) => p[1] === from && p[2] === to)?.[0] ?? (fmtRange(from, to) || placeholder);
  const close = () => { setOpen(false); ref.current?.focus(); };
  return (
    <>
      <button ref={ref} type="button" className={`dfield${from || to ? "" : " empty"} ${className}`} aria-haspopup="dialog" aria-expanded={open}
        aria-label={`${label}: ${text}`} onClick={() => setOpen((o) => !o)}>
        <CalendarDays size={15} aria-hidden /><span>{text}</span>
      </button>
      <DatePop anchor={ref.current} open={open} onClose={() => setOpen(false)} title={label} width={444}>
        <RangePicker from={from} to={to} min={min} max={max} presets={pr} onChange={(a, b) => { onChange(a, b); close(); }} />
        {clearable && (from || to) && <button type="button" className="dr-clear" onClick={() => { onChange("", ""); close(); }}>Скинути період</button>}
      </DatePop>
    </>
  );
}

/** Одна дата: «3 лист.»; clearable — кнопка «Очистити» під календарем. */
export function DateField({ value, onChange, min, max, label = "Дата", placeholder = "Оберіть дату", clearable, className = "" }: {
  value?: string | null; onChange: (iso: string) => void; min?: string; max?: string; label?: string; placeholder?: string;
  clearable?: boolean; className?: string;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const v = (value || "").slice(0, 10);
  const close = () => { setOpen(false); ref.current?.focus(); };
  return (
    <>
      <button ref={ref} type="button" className={`dfield${v ? "" : " empty"} ${className}`} aria-haspopup="dialog" aria-expanded={open}
        aria-label={`${label}: ${v ? fmtDate(v, true) : "не вибрано"}`} onClick={() => setOpen((o) => !o)}>
        <CalendarDays size={15} aria-hidden /><span>{v ? fmtDate(v, true) : placeholder}</span>
      </button>
      <DatePop anchor={ref.current} open={open} onClose={() => setOpen(false)} title={label} width={292}>
        <Calendar value={v} min={min} max={max} onPick={(d) => { onChange(d); close(); }} />
        {clearable && v && <button type="button" className="dr-clear" onClick={() => { onChange(""); close(); }}>Очистити</button>}
      </DatePop>
    </>
  );
}

// ---------------------------------------------------------------- дата й час (нагадування, передзвонити)
const normTime = (s: string) => {
  const m = /^(\d{1,2})(?:[:.\s]?(\d{2}))?$/.exec(s.trim());
  if (!m || +m[1] > 23 || +(m[2] ?? 0) > 59) return null;
  return `${pad(+m[1])}:${m[2] ?? "00"}`;
};
const HOURS = Array.from({ length: 12 }, (_, i) => `${pad(9 + i)}:00`);

/** Значення — місцевий час "YYYY-MM-DDTHH:MM" (як у старому datetime-local). Календар + чипи годин + свій час. */
export function DateTimePicker({ value, onChange, min }: { value: string; onChange: (v: string) => void; min?: string }) {
  const d = value.slice(0, 10) || isoDate(new Date());
  const t = value.slice(11, 16);
  const [own, setOwn] = useState(t);
  useEffect(() => setOwn(t), [t]);
  const commit = () => { const x = normTime(own); if (x) onChange(`${d}T${x}`); else setOwn(t); };
  return (
    <div className="dtp">
      <Calendar value={d} min={min} onPick={(x) => onChange(`${x}T${t || "10:00"}`)} />
      <div className="dtp-times" role="group" aria-label="Час">
        {HOURS.map((h) => <button key={h} type="button" className={`dr-chip${t === h ? " on" : ""}`} aria-pressed={t === h} onClick={() => onChange(`${d}T${h}`)}>{h}</button>)}
      </div>
      <label className="dtp-own"><Clock size={14} aria-hidden /><span>Свій час</span>
        <input value={own} inputMode="numeric" placeholder="14:30" maxLength={5} aria-label="Свій час, год:хв"
          onChange={(e) => setOwn(e.target.value)} onBlur={commit} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); commit(); } }} />
      </label>
    </div>
  );
}

/** «4 лист. о 10:00» для місцевого "YYYY-MM-DDTHH:MM". */
export const fmtDateTime = (v: string) => (v ? `${fmtDate(v)} о ${v.slice(11, 16)}` : "");
