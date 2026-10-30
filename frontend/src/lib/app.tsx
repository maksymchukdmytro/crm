// Спільний стан застосунку: довідники (meta), спливні повідомлення, оновлення в реальному часі.
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ROOT } from "./api";
import type { Meta } from "./types";

// ---------------------------------------------------------------- meta
export function useMeta(): Meta {
  const { data } = useQuery({ queryKey: ["meta"], queryFn: () => api.get<Meta>("/meta"), staleTime: 60_000 });
  if (!data) throw new Error("meta not loaded"); // App рендерить сторінки лише після завантаження meta
  return data;
}

export function useStatusMap() {
  const meta = useMeta();
  return Object.fromEntries(meta.statuses.map((s) => [s.id, s]));
}

// ---------------------------------------------------------------- toasts
type ToastOpts = { undo?: () => void; action?: { label: string; onClick: () => void } };
type Toast = { id: number; kind: "ok" | "error" | "warn"; text: string } & ToastOpts;
const ToastCtx = createContext<(text: string, kind?: Toast["kind"], opts?: ToastOpts) => void>(() => {});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const seq = useRef(0);
  const push = useCallback((text: string, kind: Toast["kind"] = "ok", opts: ToastOpts = {}) => {
    const id = ++seq.current;
    setItems((x) => [...x, { id, kind, text, ...opts }]);
    setTimeout(() => setItems((x) => x.filter((t) => t.id !== id)), kind === "error" ? 8000 : opts.undo || opts.action ? 6000 : 3500);
  }, []);
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="toast-wrap">
        {items.map((t) => (
          <div key={t.id} className={`flash ${t.kind}`} role="status" onClick={() => setItems((x) => x.filter((i) => i.id !== t.id))}>
            <span>{t.text}</span>
            {t.action && <button className="undo" onClick={t.action.onClick}>{t.action.label}</button>}
            {t.undo && <button className="undo" onClick={t.undo}>Скасувати</button>}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  );
}

export const useToast = () => useContext(ToastCtx);

export function errText(e: unknown): string {
  return e instanceof Error ? e.message : String(e);
}

// ---------------------------------------------------------------- realtime
// Підписка на /api/events (SSE). Подія «order» → оновити списки й картку; «product» → товари/склад.
// Якщо сервер без Redis (204) або з'єднання недоступне — інтерфейс оновлюється опитуванням раз на 30 с.
const LiveCtx = createContext<{ live: boolean }>({ live: false });
export const useLive = () => useContext(LiveCtx);

export function RealtimeProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const toast = useToast();
  const [live, setLive] = useState(false);

  useEffect(() => {
    let es: EventSource | null = null;
    let poll: number | undefined;
    let retry: number | undefined;
    let closed = false;
    let pending = new Set<string>();
    let flush: number | undefined;

    const schedule = (key: string) => {
      pending.add(key);
      if (flush) return;
      // кілька подій поспіль (масова зміна статусу) — одне оновлення
      flush = window.setTimeout(() => {
        const keys = pending;
        pending = new Set();
        flush = undefined;
        keys.forEach((k) => {
          if (k === "orders") qc.invalidateQueries({ queryKey: ["orders"] });
          else if (k === "products") { qc.invalidateQueries({ queryKey: ["products"] }); qc.invalidateQueries({ queryKey: ["warehouse"] }); qc.invalidateQueries({ queryKey: ["meta"] }); }
          else if (k.startsWith("order:")) qc.invalidateQueries({ queryKey: ["order", Number(k.slice(6))] });
        });
      }, 300);
    };

    const startPolling = () => {
      setLive(false);
      if (poll) return;
      poll = window.setInterval(() => {
        if (document.visibilityState === "visible") qc.invalidateQueries({ queryKey: ["orders"] });
      }, 30_000);
    };

    const connect = () => {
      if (closed) return;
      es = new EventSource(`${ROOT}/api/events`, { withCredentials: true });
      es.onopen = () => {
        setLive(true);
        if (poll) { clearInterval(poll); poll = undefined; }
      };
      es.onmessage = (m) => {
        try {
          const ev = JSON.parse(m.data);
          if (ev.type === "order") { schedule("orders"); schedule(`order:${ev.id}`); }
          else if (ev.type === "product") schedule("products");
          else if (ev.type === "toast") toast(ev.text, ev.kind ?? "ok");
        } catch { /* ignore */ }
      };
      es.onerror = () => {
        const wasOpen = es?.readyState === EventSource.CONNECTING;
        if (es?.readyState === EventSource.CLOSED || !wasOpen) {
          es?.close();
          startPolling();
          retry = window.setTimeout(connect, 60_000); // спробувати знову пізніше
        } else {
          setLive(false);
        }
      };
    };
    connect();
    return () => {
      closed = true;
      es?.close();
      if (poll) clearInterval(poll);
      if (retry) clearTimeout(retry);
      if (flush) clearTimeout(flush);
    };
  }, [qc, toast]);

  return <LiveCtx.Provider value={{ live }}>{children}</LiveCtx.Provider>;
}

// ---------------------------------------------------------------- дрібниці
export function useDebounced<T>(value: T, ms = 300): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

export function useHotkey(key: string, fn: (e: KeyboardEvent) => void, deps: unknown[] = []) {
  useEffect(() => {
    const h = (e: KeyboardEvent) => {
      const k = [(e.ctrlKey || e.metaKey) ? "mod" : "", e.shiftKey ? "shift" : "", e.key.toLowerCase()].filter(Boolean).join("+");
      if (k === key) fn(e);
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
}
