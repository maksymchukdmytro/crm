import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Activity, BellRing, CheckCircle2, CircleAlert, Copy, FlaskConical } from "lucide-react";
import { api, ROOT } from "../lib/api";
import { errText, useMeta, useToast } from "../lib/app";
import { ago, dt } from "../lib/format";
import type { Settings, SystemStatus, TestData } from "../lib/types";
import { Badge, Empty, Field, Kpi, Spinner, confirmAction } from "../components/ui";

const CHECK_NAMES: Record<string, string> = { database: "База даних", redis: "Redis (черга й події)", worker: "Фоновий воркер" };
const ALERT_NAMES: Record<string, string> = { sms_failed: "Помилки SMS/Viber", queue: "Переповнена черга", no_leads: "Немає нових заявок" };

export default function SystemPage() {
  const meta = useMeta();
  const qc = useQueryClient();
  const toast = useToast();
  const { data, isFetching } = useQuery({ queryKey: ["system"], queryFn: () => api.get<SystemStatus>("/system"), refetchInterval: 20_000 });
  const { data: settings } = useQuery({ queryKey: ["settings"], queryFn: () => api.get<Settings>("/settings") });
  const [f, setF] = useState<Record<string, string> | null>(null);
  const v = f ?? { alert_tg_token: settings?.values.alert_tg_token ?? "", alert_tg_chat: settings?.values.alert_tg_chat ?? "", alert_no_leads_hours: settings?.values.alert_no_leads_hours ?? "0" };
  const save = useMutation({
    mutationFn: () => api.put<Settings>("/settings/alerts", v),
    onSuccess: (s) => { qc.setQueryData(["settings"], s); setF(null); toast("Збережено"); },
    onError: (e) => toast(errText(e), "error"),
  });
  const test = useMutation({ mutationFn: () => api.post("/system/alert-test"), onSuccess: () => toast("Тестове сповіщення надіслано в Telegram"), onError: (e) => toast(errText(e), "error") });

  const td = useQuery({ queryKey: ["test-data"], queryFn: () => api.get<TestData>("/system/test-data") });
  const tdAction = useMutation({
    mutationFn: (action: "create" | "delete") => api.post<TestData>("/system/test-data", { action }),
    onSuccess: (r) => { qc.setQueryData(["test-data"], r); qc.invalidateQueries(); toast(r.message); },
    onError: (e) => toast(errText(e), "error"),
  });

  if (!data) return <Empty><Spinner /></Empty>;
  const allOk = Object.values(data.checks).every((c) => c.ok);
  const origin = window.location.origin;
  const copy = (t: string) => { navigator.clipboard?.writeText(t); toast("Скопійовано"); };

  return (
    <div>
      <div className="head"><h1><span className="h-ico"><Activity size={18} /></span>Система</h1>
        <div className="actions">{isFetching && <span className="spinner sm" />}<span className="muted">Версія {data.version}</span></div></div>

      <div className={`sys-banner ${allOk && !data.alerts.length ? "ok" : "bad"}`}>
        {allOk && !data.alerts.length ? <><CheckCircle2 size={18} /> Усе працює</> : <><CircleAlert size={18} /> Є проблеми — деталі нижче</>}
      </div>

      <div className="kpis">
        {Object.entries(data.checks).map(([k, c]) => (
          <div className="kpi" key={k}><div className="l">{CHECK_NAMES[k] ?? k}</div>
            <div className="v" style={{ fontSize: 17 }}>{c.ok ? <Badge kind="ok">працює</Badge> : <Badge kind="bad">не працює</Badge>}</div>
            <div className="s">{c.detail}</div></div>
        ))}
        <Kpi label="Задач у черзі" value={data.queue_length ?? "—"} sub={data.queue_length === null ? "без Redis" : "очікують воркера"} />
        <Kpi label="Нових заявок за 24 год" value={data.orders_today} sub={data.last_order_at ? `остання ${ago(data.last_order_at)}` : "заявок ще не було"} />
        <Kpi label="SMS/Viber за 24 год" value={(data.sms.sent ?? 0) + (data.sms.failed ?? 0) + (data.sms.queued ?? 0)}
          sub={<>{data.sms.sent ?? 0} відправлено{data.sms.failed ? <span className="lowstock"> · {data.sms.failed} помилок</span> : null}</>} />
      </div>

      <div className="grid half">
        <div className="stack">
          <div className="card">
            <h2>Активні сповіщення</h2>
            {data.alerts.length ? data.alerts.map((a) => <div key={a} className="flash error" style={{ marginBottom: 6 }}>{ALERT_NAMES[a] ?? (a.startsWith("track_") ? `Трекінг: ${meta.carriers[a.slice(6)]?.name ?? a}` : a)}</div>)
              : <p className="hint">Проблем немає.</p>}
          </div>
          <div className="card">
            <h2>Трекінг посилок</h2>
            {data.tracking ? (
              <table className="t dense"><tbody>{Object.entries(data.tracking as Record<string, { at: string; checked: number; changed: number; errors: string[]; consecutive_errors: number }>).map(([code, t]) => (
                <tr key={code}><td>{meta.carriers[code]?.name ?? code}</td><td>{dt(t.at + "Z", true)}</td><td>перевірено {t.checked}, змінено {t.changed}</td>
                  <td>{t.consecutive_errors ? <Badge kind="bad" title={t.errors[0]}>помилок поспіль: {t.consecutive_errors}</Badge> : <Badge kind="ok">ок</Badge>}</td></tr>
              ))}</tbody></table>
            ) : <p className="hint">Ще не запускався або Redis не налаштований.</p>}
          </div>
          <div className="card">
            <h2><Activity size={16} style={{ verticalAlign: -2 }} /> Зовнішній моніторинг</h2>
            <p className="hint">Додайте адресу в UptimeRobot чи подібний сервіс — він напише, якщо CRM, база, Redis або воркер перестануть працювати (відповідь 503).</p>
            <pre className="code">{`${origin}${ROOT}/healthz/full`}</pre>
            <button className="btn sm" onClick={() => copy(`${origin}${ROOT}/healthz/full`)}><Copy size={14} /> Копіювати</button>
            <h3>Помилки (Sentry)</h3>
            <p className="hint">{data.sentry ? <Badge kind="ok">увімкнено</Badge> : <Badge>вимкнено</Badge>} {data.sentry ? "Помилки сервера, воркера й браузера надсилаються в Sentry." : "Щоб увімкнути, додайте SENTRY_DSN (і SENTRY_DSN_FRONTEND для браузера) у /etc/crm/crm.env і перезапустіть служби."}</p>
            <h3>Метрики (Prometheus / Grafana)</h3>
            {data.metrics_url ? <><pre className="code">{`${origin}${data.metrics_url}\nAuthorization: Bearer <METRICS_TOKEN з /etc/crm/crm.env>`}</pre></>
              : <p className="hint">Додайте METRICS_TOKEN у /etc/crm/crm.env. Зараз метрики доступні лише вам як адміністратору: <a href={`${ROOT}/api/metrics`} target="_blank" rel="noreferrer">переглянути</a>.</p>}
          </div>
        </div>

        <div className="stack">
        <div className="card">
          <h2><FlaskConical size={16} style={{ verticalAlign: -2 }} /> Тестові дані для статистики</h2>
          <p className="hint">Додає 10 тестових товарів (артикул TEST-…) і 10 замовлень, розкиданих по останніх 30 днях, у різних статусах,
            з допродажами й UTM-мітками. Склад, SMS/Viber, чеки й маркетплейси не зачіпаються. Тестові замовлення мають сайт «test-data» —
            їх можна відфільтрувати в статистиці й видалити одним кліком.</p>
          <p>Зараз: <b>{td.data?.products ?? "…"}</b> тестових товарів, <b>{td.data?.orders ?? "…"}</b> тестових замовлень.</p>
          <div className="form-actions">
            <button className="btn" disabled={tdAction.isPending} onClick={() => tdAction.mutate("create")}>Створити 10 замовлень</button>
            {!!(td.data?.orders || td.data?.products) && <button className="btn danger" disabled={tdAction.isPending}
              onClick={() => confirmAction("Видалити всі тестові замовлення й товари? Справжні дані не зачіпаються.") && tdAction.mutate("delete")}>Видалити тестові дані</button>}
          </div>
        </div>
        <form className="card form" onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
          <h2><BellRing size={16} style={{ verticalAlign: -2 }} /> Сповіщення в Telegram</h2>
          <p className="hint">CRM напише, коли: не відправляються SMS, перевізник не відповідає 3 перевірки поспіль, черга задач переповнена, давно немає заявок з лендингів. І ще раз — коли все відновиться.</p>
          <Field label="Токен бота" hint="Створіть бота в @BotFather і вставте його токен"><input className="mono" placeholder="не вказано" value={v.alert_tg_token} onChange={(e) => setF({ ...v, alert_tg_token: e.target.value })} autoComplete="off" /></Field>
          <Field label="ID чату" hint="Напишіть боту будь-що, потім дізнайтесь ID у @userinfobot (для групи — ID групи з мінусом)"><input value={v.alert_tg_chat} onChange={(e) => setF({ ...v, alert_tg_chat: e.target.value })} /></Field>
          <Field label="Сповістити, якщо немає заявок, год" hint="Лише з 8:00 до 22:00. 0 — не стежити"><input type="number" min={0} value={v.alert_no_leads_hours} onChange={(e) => setF({ ...v, alert_no_leads_hours: e.target.value })} /></Field>
          <div className="form-actions"><button className="btn primary" disabled={save.isPending}>Зберегти</button>
            <button type="button" className="btn" onClick={() => test.mutate()} disabled={test.isPending}>Надіслати тестове</button></div>
        </form>
        </div>
      </div>
    </div>
  );
}
