import { useEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { api, qs } from "../lib/api";
import type { Status } from "../lib/types";

export function Pill({ status, children }: { status?: Status; children?: ReactNode }) {
  if (!status) return null;
  return <span className="pill" title={status.name} style={{ ["--c" as string]: status.color }}>{children ?? status.name}</span>;
}

export function Badge({ kind = "", children, title }: { kind?: "" | "ok" | "bad" | "warn" | "info"; children: ReactNode; title?: string }) {
  return <span className={`badge ${kind}`} title={title}>{children}</span>;
}

export function deliveryKind(state: string): "ok" | "bad" | "info" | "" {
  if (state === "delivered") return "ok";
  if (state === "refused" || state === "returned") return "bad";
  return state ? "info" : "";
}

export function Modal({ onClose, children, wide = false, size = "md", title }: { onClose: () => void; children: ReactNode; wide?: boolean; size?: "sm" | "md" | "lg"; title?: ReactNode }) {
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if (e.key === "Escape" && !e.defaultPrevented) onCloseRef.current(); };
    window.addEventListener("keydown", h);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { window.removeEventListener("keydown", h); document.body.style.overflow = prev; };
  }, []);
  return createPortal(
    <div className="modal" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className={`modal-box ${wide ? "wide" : size}`} role="dialog" aria-modal="true">
        <button className="modal-close" onClick={onClose} title="Закрити (Esc)"><X size={20} /></button>
        {title && <div className="modal-title">{title}</div>}
        <div className="modal-body">{children}</div>
      </div>
    </div>,
    document.body,
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <div className="empty">{children}</div>;
}

export function Spinner() {
  return <div className="spinner" aria-label="Завантаження" />;
}

export function Field({ label, children, hint }: { label: string; children: ReactNode; hint?: ReactNode }) {
  return <label><span className="lbl">{label}</span>{children}{hint && <span className="hint">{hint}</span>}</label>;
}

export function Kpi({ label, value, sub }: { label: string; value: ReactNode; sub?: ReactNode }) {
  return <div className="kpi"><div className="l">{label}</div><div className="v">{value}</div>{sub && <div className="s">{sub}</div>}</div>;
}

// ---------------------------------------------------------------- автодоповнення Нової Пошти
type Opt = { ref: string; name: string; label: string };

export function NpAutocomplete({ kind, cityRef, value, refValue, onPick, onType, placeholder }: {
  kind: "cities" | "warehouses"; cityRef?: string; value: string; refValue: string;
  onPick: (o: Opt) => void; onType: (text: string) => void; placeholder: string;
}) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Opt[]>([]);
  const [note, setNote] = useState("");
  const [hl, setHl] = useState(0);
  const seq = useRef(0);
  const timer = useRef<number | undefined>(undefined);

  const search = (q: string) => {
    if (kind === "warehouses" && !cityRef) { setItems([]); setNote("Спочатку оберіть місто зі списку"); setOpen(true); return; }
    if (kind === "cities" && q.trim().length < 2) { setOpen(false); return; }
    const my = ++seq.current;
    setNote("Пошук…"); setOpen(true);
    api.get<{ ok: boolean; items?: Opt[]; error?: string }>(`/np/${kind}${qs({ q, city_ref: cityRef })}`)
      .then((d) => {
        if (my !== seq.current) return;
        if (!d.ok) { setItems([]); setNote(d.error ?? "Помилка"); return; }
        setItems(d.items ?? []); setHl(0); setNote(d.items?.length ? "" : "Нічого не знайдено");
      })
      .catch((e) => { if (my === seq.current) { setItems([]); setNote(String(e.message ?? e)); } });
  };

  const pick = (o?: Opt) => { if (!o) return; onPick(o); setOpen(false); };

  return (
    <div className="ac">
      <input value={value} placeholder={placeholder} className={refValue ? "ok" : ""}
        onChange={(e) => { onType(e.target.value); clearTimeout(timer.current); const v = e.target.value; timer.current = window.setTimeout(() => search(v), 280); }}
        onFocus={() => { if (!refValue && kind === "warehouses") search(value); }}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        onKeyDown={(e) => {
          if (!open || !items.length) return;
          if (e.key === "ArrowDown") { e.preventDefault(); setHl((h) => (h + 1) % items.length); }
          else if (e.key === "ArrowUp") { e.preventDefault(); setHl((h) => (h - 1 + items.length) % items.length); }
          else if (e.key === "Enter") { e.preventDefault(); pick(items[hl]); }
          else if (e.key === "Escape") { e.preventDefault(); setOpen(false); }
        }} />
      {open && (
        <div className="ac-list on">
          {note && <div className="note">{note}</div>}
          {items.map((o, i) => (
            <div key={o.ref} className={i === hl ? "hl" : ""} onMouseDown={(e) => { e.preventDefault(); pick(o); }}>{o.label || o.name}</div>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- підтвердження
export function confirmAction(text: string): boolean {
  return window.confirm(text);
}
