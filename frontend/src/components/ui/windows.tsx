// Вікна поверх сторінки (велике, середнє, мале) і бічна панель 360 px. Esc закриває, фокус лишається у вікні.
import { useEffect, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";
import { IconButton } from "./buttons";

let openCount = 0;

function useWindowBehaviour(onClose: () => void, ref: React.RefObject<HTMLElement | null>) {
  const cb = useRef(onClose);
  cb.current = onClose;
  useEffect(() => {
    const prevFocus = document.activeElement as HTMLElement | null;
    openCount++;
    const myLevel = openCount;
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !e.defaultPrevented && myLevel === openCount) { e.preventDefault(); cb.current(); }
      if (e.key === "Tab" && ref.current && myLevel === openCount) {             // фокус не виходить за межі вікна
        const f = ref.current.querySelectorAll<HTMLElement>('a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),textarea:not([disabled]),[tabindex]:not([tabindex="-1"])');
        if (!f.length) return;
        const first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    };
    window.addEventListener("keydown", key);
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    if (ref.current && !ref.current.contains(document.activeElement)) {
      const auto = ref.current.querySelector<HTMLElement>("[data-autofocus]");
      (auto ?? ref.current).focus({ preventScroll: true });
    }
    return () => {
      openCount--;
      window.removeEventListener("keydown", key);
      document.body.style.overflow = prevOverflow;
      prevFocus?.focus?.({ preventScroll: true });
    };
  }, [ref]);
}

export function Window({ onClose, title, head, actions, footer, children, size = "md", label, bodyClass = "", className = "" }: {
  onClose: () => void; title?: ReactNode; head?: ReactNode; actions?: ReactNode; footer?: ReactNode; children: ReactNode;
  size?: "sm" | "md" | "lg" | "xl"; label?: string; bodyClass?: string; className?: string;
}) {
  const box = useRef<HTMLDivElement>(null);
  useWindowBehaviour(onClose, box);
  return createPortal(
    <div className="win-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div ref={box} className={`win ${size} ${className}`} role="dialog" aria-modal="true" aria-label={label ?? (typeof title === "string" ? title : undefined)} tabIndex={-1}>
        {head ?? (
          <div className="win-head">
            {title && <h2>{title}</h2>}
            <div className="acts">{actions}<IconButton icon={X} label="Закрити (Esc)" quiet onClick={onClose} /></div>
          </div>
        )}
        <div className={`win-body ${bodyClass}`}>{children}</div>
        {footer && <div className="win-foot">{footer}</div>}
      </div>
    </div>,
    document.body,
  );
}

export function SidePanel({ onClose, title, children, footer }: { onClose: () => void; title: ReactNode; children: ReactNode; footer?: ReactNode }) {
  const box = useRef<HTMLDivElement>(null);
  useWindowBehaviour(onClose, box);
  return createPortal(
    <aside ref={box} className="side-panel" role="dialog" aria-modal="true" aria-label={typeof title === "string" ? title : undefined} tabIndex={-1}>
      <div className="win-head"><h2 style={{ fontSize: 15 }}>{title}</h2><div className="acts"><IconButton icon={X} label="Закрити (Esc)" quiet onClick={onClose} /></div></div>
      <div className="win-body">{children}</div>
      {footer && <div className="win-foot">{footer}</div>}
    </aside>,
    document.body,
  );
}
