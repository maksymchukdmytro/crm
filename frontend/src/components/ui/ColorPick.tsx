// Вибір кольору (етап A3, docs/UI-NEXT.md): кружок поточного кольору; клік — 12 кольорів CRM і поле свого HEX.
// Замість системного <input type="color">. Спливає поверх усього (Floating), на телефоні — більші цілі.
import { useRef, useState } from "react";
import { Floating } from "./HoverCard";

export const CRM_COLORS = ["#2E6BE6", "#16A34A", "#D97706", "#7C3AED", "#DC2626", "#7C7B76",
  "#0D9488", "#DB2777", "#0EA5E9", "#A16207", "#1F1F1C", "#64748B"];

const norm = (v: string) => {
  const s = v.trim().replace(/^#?/, "#");
  return /^#[0-9a-fA-F]{6}$/.test(s) ? s.toUpperCase() : /^#[0-9a-fA-F]{3}$/.test(s) ? `#${s.slice(1).split("").map((c) => c + c).join("")}`.toUpperCase() : null;
};

export function ColorPick({ value, onChange, label = "Колір", colors = CRM_COLORS, disabled }: {
  value: string; onChange: (hex: string) => void; label?: string; colors?: string[]; disabled?: boolean;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const [own, setOwn] = useState(value || "");
  const cur = (value || "").toUpperCase();
  const pick = (c: string) => { onChange(c); setOpen(false); ref.current?.focus(); };
  return (
    <>
      <button ref={ref} type="button" className="cpick" disabled={disabled} aria-label={`${label}: ${cur || "не вибрано"}`} aria-expanded={open}
        onClick={(e) => { e.stopPropagation(); setOwn(value || ""); setOpen((x) => !x); }}>
        <i style={{ background: value || "transparent" }} />
      </button>
      <Floating anchor={ref.current} open={open} onClose={() => setOpen(false)} width={typeof window !== "undefined" && window.matchMedia("(max-width: 768px)").matches ? 324 : 236} className="cpick-pop" label={label}>
        <div className="cpick-grid" role="listbox" aria-label={label}>
          {colors.map((c) => (
            <button key={c} type="button" role="option" aria-selected={cur === c.toUpperCase()} aria-label={c} title={c}
              className={cur === c.toUpperCase() ? "on" : ""} style={{ background: c, ["--c" as string]: c }} onClick={() => pick(c)} />
          ))}
        </div>
        <form className="cpick-own" onSubmit={(e) => { e.preventDefault(); const h = norm(own); if (h) pick(h); }}>
          <i style={{ background: norm(own) ?? "transparent" }} />
          <input value={own} onChange={(e) => setOwn(e.target.value)} placeholder="#2E6BE6" maxLength={7} aria-label="Свій колір, HEX"
            onBlur={() => { const h = norm(own); if (h && h !== cur) onChange(h); }} />
        </form>
      </Floating>
    </>
  );
}
