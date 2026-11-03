// Підказка-картка при наведенні (макет v26, «А» і «Б»): значок у рядку, а подробиці — у картці поверх усього.
// Наведення показує картку через 180 мс; з неї можна перейти мишею й натиснути кнопку. Клік по значку закріплює картку
// (для дотику й клавіатури), Esc чи клік поза нею — закриває. Список рендериться в body (portal), тож не обрізається таблицею.
import { useEffect, useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { createPortal } from "react-dom";

type Place = { left: number; top?: number; bottom?: number; maxHeight: number };

function place(anchor: DOMRect, width: number, height: number): Place {
  const below = window.innerHeight - anchor.bottom - 8;
  const up = below < Math.min(height, 260) && anchor.top > below;
  let left = anchor.left + anchor.width / 2 - width / 2;
  left = Math.max(8, Math.min(left, window.innerWidth - width - 8));
  return up ? { left, bottom: window.innerHeight - anchor.top + 6, maxHeight: anchor.top - 14 } : { left, top: anchor.bottom + 6, maxHeight: below - 6 };
}

/** Плаваюча картка біля елемента: для підказок при наведенні й меню, яким тісно в клітинці таблиці. */
export function Floating({ anchor, open, onClose, width = 280, className = "", children, onEnter, onLeave, role = "dialog", label }: {
  anchor: HTMLElement | null; open: boolean; onClose: () => void; width?: number; className?: string; children: ReactNode;
  onEnter?: () => void; onLeave?: () => void; role?: string; label?: string;
}) {
  const box = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<Place | null>(null);
  useLayoutEffect(() => {
    if (!open || !anchor) return;
    const upd = () => {
      const r = anchor.getBoundingClientRect();
      if (r.bottom < 0 || r.top > window.innerHeight) { onClose(); return; }
      setPos(place(r, width, box.current?.offsetHeight ?? 200));
    };
    upd();
    window.addEventListener("resize", upd);
    document.addEventListener("scroll", upd, true);
    return () => { window.removeEventListener("resize", upd); document.removeEventListener("scroll", upd, true); };
  }, [open, anchor, width]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (!open) return;
    const away = (e: Event) => {
      const t = e.target as Node;
      if (box.current?.contains(t) || anchor?.contains(t)) return;
      onClose();
    };
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") { e.stopPropagation(); onClose(); anchor?.focus(); } };
    document.addEventListener("mousedown", away, true);
    document.addEventListener("touchstart", away, true);
    document.addEventListener("keydown", esc, true);
    return () => {
      document.removeEventListener("mousedown", away, true);
      document.removeEventListener("touchstart", away, true);
      document.removeEventListener("keydown", esc, true);
    };
  }, [open, anchor, onClose]);
  if (!open || !anchor) return null;
  const style: CSSProperties = { width, ...(pos ?? { left: -9999, top: 0 }), visibility: pos ? "visible" : "hidden" };
  return createPortal(
    <div ref={box} className={`hc ${className}`} role={role} aria-label={label} style={style}
      onMouseEnter={onEnter} onMouseLeave={onLeave} onClick={(e) => e.stopPropagation()}>
      {children}
    </div>,
    document.body,
  );
}

/** Значок, що при наведенні (або кліку) показує картку з подробицями. */
export function HoverCard({ trigger, children, label, width = 280, className = "", triggerClass = "" }: {
  trigger: ReactNode; children: ReactNode | (() => ReactNode); label: string; width?: number; className?: string; triggerClass?: string;
}) {
  const ref = useRef<HTMLButtonElement>(null);
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const t = useRef<number>(0);
  const show = () => { window.clearTimeout(t.current); t.current = window.setTimeout(() => setOpen(true), 180); };
  const hide = () => { window.clearTimeout(t.current); if (!pinned) t.current = window.setTimeout(() => setOpen(false), 160); };
  const stay = () => window.clearTimeout(t.current);
  useEffect(() => () => window.clearTimeout(t.current), []);
  const close = () => { setOpen(false); setPinned(false); };
  return (
    <>
      <button ref={ref} type="button" className={`hc-t ${triggerClass}${open ? " on" : ""}`} aria-label={label} aria-expanded={open}
        onMouseEnter={show} onMouseLeave={hide}
        onClick={(e) => { e.stopPropagation(); window.clearTimeout(t.current); setPinned(!pinned || !open); setOpen(!(pinned && open)); }}>
        {trigger}
      </button>
      <Floating anchor={ref.current} open={open} onClose={close} width={width} className={className} onEnter={stay} onLeave={hide} label={label}>
        {typeof children === "function" ? children() : children}
      </Floating>
    </>
  );
}
