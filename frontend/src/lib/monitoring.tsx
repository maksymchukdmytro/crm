// Помилки в браузері → Sentry (лише якщо сервер передав DSN), і «запобіжник» для React:
// помилка в одному розділі не ламає весь застосунок, а показує повідомлення з кнопкою «Оновити».
import { Component, type ErrorInfo, type ReactNode } from "react";

declare global {
  interface Window { CRM_SENTRY?: { dsn: string; env: string; release: string } }
}

let sentry: typeof import("@sentry/react") | null = null;

export async function initMonitoring() {
  const cfg = window.CRM_SENTRY;
  if (!cfg?.dsn) return;
  try {
    // окремий файл, який завантажується лише коли Sentry увімкнено
    const S = await import("@sentry/react");
    // персональні дані (IP, cookie) браузерний SDK за замовчуванням не надсилає
    S.init({ dsn: cfg.dsn, environment: cfg.env, release: `crm@${cfg.release}`, tracesSampleRate: 0 });
    sentry = S;
  } catch { /* моніторинг не повинен ламати застосунок */ }
}

export function report(e: unknown, extra?: Record<string, unknown>) {
  sentry?.captureException(e, extra ? { extra } : undefined);
  console.error(e);
}

export class ErrorBoundary extends Component<{ children: ReactNode; area?: string }, { error: Error | null }> {
  state = { error: null as Error | null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  componentDidCatch(error: Error, info: ErrorInfo) { report(error, { area: this.props.area, stack: info.componentStack }); }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="empty big">
        <h1>Щось пішло не так</h1>
        <p>Помилку вже зафіксовано. Спробуйте оновити сторінку — збережені дані не втрачено.</p>
        <p className="hint mono">{this.state.error.message}</p>
        <button className="btn primary" onClick={() => location.reload()}>Оновити сторінку</button>
      </div>
    );
  }
}
