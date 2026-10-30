import { useEffect, useState, type RefObject } from "react";

/** Клік поза елементом або Esc — закрити поповер. */
export function useOutside(ref: RefObject<HTMLElement | null>, onOut: () => void, active = true) {
  useEffect(() => {
    if (!active) return;
    const down = (e: MouseEvent | TouchEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) onOut(); };
    const key = (e: KeyboardEvent) => { if (e.key === "Escape") { e.stopPropagation(); onOut(); } };
    document.addEventListener("mousedown", down);
    document.addEventListener("touchstart", down);
    document.addEventListener("keydown", key, true);
    return () => {
      document.removeEventListener("mousedown", down);
      document.removeEventListener("touchstart", down);
      document.removeEventListener("keydown", key, true);
    };
  }, [ref, onOut, active]);
}

/** Чи фокус зараз у полі вводу (глобальні клавіші там не спрацьовують). */
export function inField(e: KeyboardEvent): boolean {
  const t = e.target as HTMLElement | null;
  if (!t) return false;
  return t.isContentEditable || ["INPUT", "TEXTAREA", "SELECT"].includes(t.tagName);
}

/** Телефон (≤ 768 px): списки стають картками, вікна — на весь екран. */
export function useMobile(query = "(max-width: 768px)"): boolean {
  const [m, setM] = useState(() => typeof window !== "undefined" && window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const on = () => setM(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, [query]);
  return m;
}
