// Клієнт JSON API. Cookie сесії + заголовок X-CRM (захист від CSRF).
declare global {
  interface Window { CRM_ROOT?: string }
}

export const ROOT: string = (window.CRM_ROOT ?? "").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type Body = Record<string, unknown> | unknown[] | FormData | undefined;

async function request<T>(method: string, path: string, body?: Body): Promise<T> {
  const headers: Record<string, string> = { "X-CRM": "1", Accept: "application/json" };
  let payload: BodyInit | undefined;
  if (body instanceof FormData) payload = body;
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  let res: Response;
  try {
    res = await fetch(`${ROOT}/api${path}`, { method, headers, body: payload, credentials: "same-origin" });
  } catch {
    throw new ApiError(0, "Немає з'єднання з сервером");
  }
  if (res.status === 401) window.dispatchEvent(new CustomEvent("crm:unauthorized"));
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  let data: unknown = null;
  try { data = text ? JSON.parse(text) : null; } catch { /* не JSON */ }
  if (!res.ok) {
    const msg = (data && typeof data === "object" && "error" in data) ? String((data as { error: unknown }).error) : `Помилка ${res.status}`;
    throw new ApiError(res.status, msg);
  }
  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: Body) => request<T>("POST", path, body ?? {}),
  patch: <T>(path: string, body: Body) => request<T>("PATCH", path, body),
  put: <T>(path: string, body: Body) => request<T>("PUT", path, body),
  del: <T>(path: string) => request<T>("DELETE", path),
};

export function qs(params: Record<string, string | number | boolean | undefined | null>): string {
  const u = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "" && v !== false) u.set(k, String(v));
  }
  const s = u.toString();
  return s ? `?${s}` : "";
}
