// Підказка CRM (етап A7, docs/UI-NEXT.md) замість системного title: темна плашка 12 px над елементом, через 400 мс.
// Один шар на весь застосунок (<TooltipLayer /> у корені): атрибут title будь-якого елемента при наведенні переноситься
// в data-tip (щоб не вилазила системна підказка), а значкам без підпису — ще й в aria-label, щоб назва не губилась.
// Обрізаний текст (title = сам текст) показуємо, лише коли його справді обрізано. На дотик підказки не показуємо.
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

type Tip = { text: string; x: number; y: number; below: boolean };

function tipOf(el: HTMLElement): string | null {
  const t = el.getAttribute("title");
  if (t != null) {
    el.removeAttribute("title");
    if (t.trim()) {
      el.dataset.tip = t;
      if (!el.getAttribute("aria-label") && !el.textContent?.trim() && !el.querySelector("img[alt]:not([alt=''])")) el.setAttribute("aria-label", t);
    } else delete el.dataset.tip;
  }
  const tip = el.dataset.tip;
  if (!tip) return null;
  // обрізаний текст: підказка лише коли текст не вміщується
  if (tip.trim() === el.textContent?.trim() && el.scrollWidth <= el.clientWidth + 1) return null;
  return tip;
}

export function TooltipLayer() {
  const [tip, setTip] = useState<Tip | null>(null);
  const timer = useRef<number>(0);
  const cur = useRef<HTMLElement | null>(null);
  useEffect(() => {
    const show = (el: HTMLElement, delay: number) => {
      window.clearTimeout(timer.current);
      const text = tipOf(el);
      cur.current = el;
      if (!text) { setTip(null); return; }
      timer.current = window.setTimeout(() => {
        if (cur.current !== el || !el.isConnected) return;
        const r = el.getBoundingClientRect();
        const below = r.top < 44;
        setTip({ text, x: r.left + r.width / 2, y: below ? r.bottom + 6 : r.top - 6, below });
      }, delay);
    };
    const hide = () => { window.clearTimeout(timer.current); cur.current = null; setTip(null); };
    const over = (e: PointerEvent) => {
      if (e.pointerType !== "mouse") return;
      const el = (e.target as Element | null)?.closest?.<HTMLElement>("[title], [data-tip]");
      if (el === cur.current) return;
      if (!el || el.closest("option, iframe, svg")) { hide(); return; }
      show(el, 400);
    };
    const focus = (e: FocusEvent) => {
      const el = e.target as HTMLElement;
      if (!el.matches?.(":focus-visible") || !el.matches("[title], [data-tip]")) return;
      show(el, 150);
    };
    document.addEventListener("pointerover", over, true);
    document.addEventListener("focusin", focus, true);
    document.addEventListener("focusout", hide, true);
    document.addEventListener("pointerdown", hide, true);
    document.addEventListener("keydown", hide, true);
    document.addEventListener("scroll", hide, true);
    window.addEventListener("blur", hide);
    return () => {
      document.removeEventListener("pointerover", over, true);
      document.removeEventListener("focusin", focus, true);
      document.removeEventListener("focusout", hide, true);
      document.removeEventListener("pointerdown", hide, true);
      document.removeEventListener("keydown", hide, true);
      document.removeEventListener("scroll", hide, true);
      window.removeEventListener("blur", hide);
      window.clearTimeout(timer.current);
    };
  }, []);
  return <TipBox tip={tip} />;
}

function TipBox({ tip }: { tip: Tip | null }) {
  const box = useRef<HTMLDivElement>(null);
  const [left, setLeft] = useState<number | null>(null);
  useEffect(() => {
    if (!tip || !box.current) { setLeft(null); return; }
    const w = box.current.offsetWidth;
    setLeft(Math.max(8, Math.min(tip.x - w / 2, window.innerWidth - w - 8)));
  }, [tip]);
  if (!tip) return null;
  return createPortal(
    <div ref={box} className={`tip${tip.below ? " below" : ""}`} role="tooltip"
      style={{ left: left ?? -9999, top: tip.y, visibility: left == null ? "hidden" : "visible" }}>{tip.text}</div>,
    document.body,
  );
}
