// Панель масових дій, кнопка «+» з меню швидких дій, меню-поповер.
import { useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Plus, X } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useOutside } from "./hooks";

export function BulkBar({ count, onClear, children, primary }: { count: number; onClear: () => void; children?: ReactNode; primary?: ReactNode }) {
  if (!count) return null;
  return createPortal(
    <div className="bulkbar" role="toolbar" aria-label={`Вибрано ${count}`}>
      <span className="sel-n"><input type="checkbox" checked readOnly aria-hidden tabIndex={-1} />Вибрано {count}</span>
      {children}
      <button type="button" className="btn quiet sm" onClick={onClear}><X size={14} />Зняти</button>
      {primary && <span className="primary-act">{primary}</span>}
    </div>,
    document.body,
  );
}

export type QuickAction = { key: string; label: string; icon: LucideIcon; kbd?: string; onClick: () => void };

/** Клік — головна дія; наведення або довге натискання — меню швидких дій. */
export function Fab({ onClick, actions, label = "Нове замовлення" }: { onClick: () => void; actions: QuickAction[]; label?: string }) {
  const [open, setOpen] = useState(false);
  const wrap = useRef<HTMLDivElement>(null);
  const hoverT = useRef<number | undefined>(undefined);
  const pressT = useRef<number | undefined>(undefined);
  const longPressed = useRef(false);
  useOutside(wrap, () => setOpen(false), open);
  return (
    <div className="fab-wrap" ref={wrap}
      onMouseEnter={() => { clearTimeout(hoverT.current); hoverT.current = window.setTimeout(() => setOpen(true), 350); }}
      onMouseLeave={() => { clearTimeout(hoverT.current); hoverT.current = window.setTimeout(() => setOpen(false), 250); }}>
      {open && (
        <div className="pop fab-menu" role="menu">
          {actions.map((a) => (
            <button key={a.key} role="menuitem" className="pop-item" onClick={() => { setOpen(false); a.onClick(); }}>
              <a.icon size={16} />{a.label}{a.kbd && <kbd>{a.kbd}</kbd>}
            </button>
          ))}
        </div>
      )}
      <button type="button" className={`fab${open ? " open" : ""}`} aria-label={label} title={`${label} (N)`} aria-haspopup="menu" aria-expanded={open}
        onTouchStart={() => { longPressed.current = false; pressT.current = window.setTimeout(() => { longPressed.current = true; setOpen(true); }, 450); }}
        onTouchEnd={() => clearTimeout(pressT.current)}
        onClick={() => { if (longPressed.current) { longPressed.current = false; return; } setOpen(false); onClick(); }}>
        <Plus size={24} strokeWidth={2.2} />
      </button>
    </div>
  );
}

/** Кнопка з випадним меню (Друк ▾, «⋯»). Меню відкривається вгору, якщо внизу мало місця. */
export function MenuButton({ button, children, align = "right", className = "" }: {
  button: (p: { open: boolean; toggle: () => void }) => ReactNode; children: (close: () => void) => ReactNode; align?: "left" | "right"; className?: string;
}) {
  const [open, setOpen] = useState(false);
  const [up, setUp] = useState(false);
  const wrap = useRef<HTMLDivElement>(null);
  useOutside(wrap, () => setOpen(false), open);
  const toggle = () => {
    if (!open && wrap.current) setUp(window.innerHeight - wrap.current.getBoundingClientRect().bottom < 260);
    setOpen((o) => !o);
  };
  return (
    <div className={`menu-btn ${className}`} ref={wrap}>
      {button({ open, toggle })}
      {open && <div className={`pop menu-pop ${align}${up ? " up" : ""}`} role="menu">{children(() => setOpen(false))}</div>}
    </div>
  );
}
