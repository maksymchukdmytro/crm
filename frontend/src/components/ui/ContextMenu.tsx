// Контекстне меню (етап A6, docs/UI-NEXT.md): правий клік (або клавіша меню / Shift F10) по рядку чи картці
// відкриває те саме меню, що «⋯», — у вигляді спливаючих меню CRM. Не виходить за край екрана, ↑↓ Enter Esc.
import { useEffect, useLayoutEffect, useRef, useState, type ReactNode, type RefObject } from "react";
import { createPortal } from "react-dom";

const ITEMS = ".pop-item:not(:disabled), [role=menuitem]:not(:disabled), [role=menuitemradio]:not(:disabled)";

/** ↑↓ Home End між пунктами меню й пошук першою літерою. */
export function useMenuKeys(box: RefObject<HTMLElement | null>, active = true) {
  useEffect(() => {
    const el = box.current;
    if (!active || !el) return;
    const key = (e: KeyboardEvent) => {
      const items = [...el.querySelectorAll<HTMLElement>(ITEMS)];
      if (!items.length) return;
      const i = items.indexOf(document.activeElement as HTMLElement);
      let next = -1;
      if (e.key === "ArrowDown") next = (i + 1) % items.length;
      else if (e.key === "ArrowUp") next = i <= 0 ? items.length - 1 : i - 1;
      else if (e.key === "Home") next = 0;
      else if (e.key === "End") next = items.length - 1;
      else if (e.key.length === 1 && /\S/.test(e.key) && !(e.target instanceof HTMLInputElement)) {
        const k = e.key.toLowerCase();
        const order = [...items.slice(i + 1), ...items.slice(0, i + 1)];
        const hit = order.find((x) => x.textContent?.trim().toLowerCase().startsWith(k));
        if (hit) next = items.indexOf(hit);
      }
      if (next >= 0) { e.preventDefault(); items[next].focus(); }
    };
    el.addEventListener("keydown", key);
    return () => el.removeEventListener("keydown", key);
  }, [box, active]);
}

export function ContextMenu({ x, y, onClose, label, children }: {
  x: number; y: number; onClose: () => void; label?: string; children: (close: () => void) => ReactNode;
}) {
  const box = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState<{ left: number; top: number } | null>(null);
  const cb = useRef(onClose);
  cb.current = onClose;
  useMenuKeys(box);
  useLayoutEffect(() => {
    const b = box.current;
    if (!b) return;
    const w = b.offsetWidth, h = b.offsetHeight;
    const left = Math.max(8, Math.min(x, window.innerWidth - w - 8));
    const top = y + h > window.innerHeight - 8 ? Math.max(8, y - h) : y;
    if (!pos || pos.left !== left || pos.top !== top) setPos({ left, top });
  });
  const shown = pos != null;
  useEffect(() => {
    if (shown) box.current?.querySelector<HTMLElement>(ITEMS)?.focus({ preventScroll: true });
  }, [shown]);
  useEffect(() => {
    const away = (e: Event) => { if (!box.current?.contains(e.target as Node)) cb.current(); };
    const esc = (e: KeyboardEvent) => { if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); cb.current(); } };
    const gone = () => cb.current();
    document.addEventListener("mousedown", away, true);
    document.addEventListener("touchstart", away, true);
    document.addEventListener("keydown", esc, true);
    window.addEventListener("resize", gone);
    document.addEventListener("scroll", gone, true);
    return () => {
      document.removeEventListener("mousedown", away, true);
      document.removeEventListener("touchstart", away, true);
      document.removeEventListener("keydown", esc, true);
      window.removeEventListener("resize", gone);
      document.removeEventListener("scroll", gone, true);
    };
  }, []);
  return createPortal(
    <div ref={box} className="pop ctx-menu" role="menu" aria-label={label} onContextMenu={(e) => e.preventDefault()}
      style={pos ? { left: pos.left, top: pos.top } : { left: -9999, top: 0, visibility: "hidden" }}>
      {children(onClose)}
    </div>,
    document.body,
  );
}

/** Де показати меню для події contextmenu: у точці кліку або (з клавіатури) під елементом. */
export function menuPoint(e: { clientX: number; clientY: number; currentTarget: EventTarget | null; target: EventTarget | null }, el?: HTMLElement | null) {
  if (e.clientX || e.clientY) return { x: e.clientX, y: e.clientY };
  const r = (el ?? (e.target as HTMLElement)).getBoundingClientRect();
  return { x: r.left + 24, y: r.bottom - 4 };
}
