import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Plus, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import { errText, useMeta, useToast } from "../lib/app";
import { dt, phone } from "../lib/format";
import type { Settings, Status, User } from "../lib/types";
import { Badge, Empty, Field, NpAutocomplete, Spinner } from "../components/ui";

type S = Settings;
const TABS = { general: "Загальні", webhook: "Прийом заявок", delivery: "Доставка", sms: "SMS / Viber", statuses: "Статуси", users: "Користувачі" };

export default function SettingsPage() {
  const [tab, setTab] = useState<keyof typeof TABS>(() => (localStorage.getItem("crm-settings-tab") as keyof typeof TABS) || "general");
  const { data } = useQuery({ queryKey: ["settings"], queryFn: () => api.get<S>("/settings") });
  const choose = (t: keyof typeof TABS) => { setTab(t); localStorage.setItem("crm-settings-tab", t); };
  return (
    <div>
      <div className="head"><h1>Налаштування</h1></div>
      <nav className="subnav">{Object.entries(TABS).map(([k, n]) => <a key={k} className={tab === k ? "on" : ""} onClick={() => choose(k as keyof typeof TABS)}>{n}</a>)}</nav>
      {!data ? <Empty><Spinner /></Empty> : <>
        {tab === "general" && <General s={data} />}
        {tab === "webhook" && <Webhook s={data} />}
        {tab === "delivery" && <Delivery s={data} />}
        {tab === "sms" && <Sms s={data} />}
        {tab === "statuses" && <Statuses s={data} />}
        {tab === "users" && <Users s={data} />}
      </>}
    </div>
  );
}

function useSave() {
  const qc = useQueryClient();
  const toast = useToast();
  return useMutation({
    mutationFn: ({ path, body, method = "put" }: { path: string; body?: unknown; method?: "put" | "post" | "del" }) =>
      method === "del" ? api.del<S>(path) : method === "post" ? api.post<S>(path, body as Record<string, unknown>) : api.put<S>(path, body as Record<string, unknown>),
    onSuccess: (s) => { if (s?.values) qc.setQueryData(["settings"], s); qc.invalidateQueries({ queryKey: ["meta"] }); toast(s?.message ?? "Збережено"); },
    onError: (e) => toast(errText(e), "error"),
  });
}

function useForm(s: S, keys: string[]) {
  const [v, setV] = useState<Record<string, string>>(() => Object.fromEntries(keys.map((k) => [k, s.values[k] ?? ""])));
  const bind = (k: string) => ({ value: v[k] ?? "", onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => setV({ ...v, [k]: e.target.value }) });
  const check = (k: string) => ({ checked: v[k] === "1", onChange: (e: React.ChangeEvent<HTMLInputElement>) => setV({ ...v, [k]: e.target.checked ? "1" : "0" }) });
  return { v, setV, bind, check };
}

function Secret({ label, k, bind, hint }: { label: string; k: string; bind: (k: string) => object; hint?: string }) {
  return <Field label={label} hint={hint}><input className="mono" autoComplete="off" placeholder="не вказано" {...bind(k)} /></Field>;
}

function General({ s }: { s: S }) {
  const save = useSave();
  const { v, bind, check } = useForm(s, ["company_name", "duplicate_days", "auto_assign", "managers_see_own_only", "auto_status_from_tracking", "tracking_interval_min"]);
  return (
    <form className="card form narrow" onSubmit={(e) => { e.preventDefault(); save.mutate({ path: "/settings/general", body: v }); }}>
      <Field label="Назва компанії"><input {...bind("company_name")} /></Field>
      <Field label="Пошук дублів за телефоном, днів" hint="0 — вимкнути"><input type="number" min={0} {...bind("duplicate_days")} /></Field>
      <Field label="Розподіл нових заявок"><select {...bind("auto_assign")}><option value="off">Вручну — менеджер бере сам</option><option value="round_robin">По черзі між менеджерами</option></select></Field>
      <Field label="Перевіряти статуси посилок кожні, хв"><input type="number" min={5} {...bind("tracking_interval_min")} /></Field>
      <div className="checks">
        <label className="check"><input type="checkbox" {...check("managers_see_own_only")} /> Менеджери бачать лише свої та нерозподілені замовлення</label>
        <label className="check"><input type="checkbox" {...check("auto_status_from_tracking")} /> Змінювати статус за трекінгом (Відправлено → Отримано / Відмова)</label>
      </div>
      <div className="form-actions"><button className="btn primary" disabled={save.isPending}>Зберегти</button></div>
    </form>
  );
}

function Webhook({ s }: { s: S }) {
  const save = useSave();
  const toast = useToast();
  const url = s.webhook_url;
  const copy = () => { navigator.clipboard?.writeText(url); toast("Адресу скопійовано"); };
  const form = `<form method="post" action="${url}">
  <input name="name" placeholder="Ваше ім'я" required>
  <input name="phone" placeholder="Телефон" required>
  <input type="hidden" name="sku" value="ART-001">
  <input type="hidden" name="site" value="landing-1">
  <input type="hidden" name="redirect" value="https://ваш-сайт/thanks.html">
  <button>Замовити</button>
</form>
<script>
var p = new URLSearchParams(location.search), f = document.forms[0];
["utm_source","utm_medium","utm_campaign","utm_content","utm_term"].forEach(function (k) {
  if (p.get(k)) { var i = document.createElement("input"); i.type = "hidden"; i.name = k; i.value = p.get(k); f.appendChild(i); }
});
</script>`;
  return (
    <div className="grid half">
      <div className="card">
        <h2>Адреса для заявок</h2>
        <p className="hint">POST-запит з форми лендингу, конструктора сайтів або вашого сервера.</p>
        <pre className="code">{url}</pre>
        <div className="row"><button className="btn sm" onClick={copy}><Copy size={14} /> Копіювати</button>
          <button className="btn sm danger" onClick={() => { if (window.confirm("Старий ключ перестане працювати. Продовжити?")) save.mutate({ path: "/settings/webhook/regenerate", method: "post" }); }}>Створити новий ключ</button></div>
        <h3>Поля</h3>
        <table className="t dense"><tbody>
          <tr><td><code>name</code></td><td>ПІБ клієнта</td></tr><tr><td><code>phone</code></td><td>Телефон (обов'язково)</td></tr>
          <tr><td><code>sku</code> / <code>product_id</code></td><td>Товар, <code>qty</code> і <code>price</code> — кількість і ціна</td></tr>
          <tr><td><code>products</code></td><td>Кілька товарів: <code>[{"{"}"sku":"A1","qty":1{"}"}]</code></td></tr>
          <tr><td><code>comment</code>, <code>site</code></td><td>Коментар, назва лендингу</td></tr>
          <tr><td><code>utm_*</code></td><td>Мітки реклами</td></tr><tr><td><code>redirect</code></td><td>Сторінка «Дякуємо» після HTML-форми</td></tr>
        </tbody></table>
      </div>
      <div className="card"><h2>Приклад HTML-форми</h2><pre className="code">{form}</pre>
        <h3>JSON</h3><pre className="code">{`curl -X POST '${url}' -H 'Content-Type: application/json' \\\n  -d '{"name":"Іван","phone":"0671234567","sku":"ART-001","utm_source":"facebook"}'`}</pre></div>
    </div>
  );
}

function Delivery({ s }: { s: S }) {
  const save = useSave();
  const np = useForm(s, ["np_api_key", "np_city_name", "np_city_ref", "np_warehouse_name", "np_warehouse_ref", "np_sender_phone", "np_cod_mode", "np_payer", "np_default_weight", "np_seat_size", "np_description"]);
  const up = useForm(s, ["up_bearer", "up_token", "up_tracking_bearer", "up_sender_uuid", "up_sandbox", "up_type"]);
  const me = useForm(s, ["meest_username", "meest_password", "meest_sender_branch_id", "meest_sender_name", "meest_sender_phone"]);
  return (
    <div className="grid half">
      <form className="card form" onSubmit={(e) => { e.preventDefault(); save.mutate({ path: "/settings/np", body: np.v }); }}>
        <h2>Нова Пошта</h2>
        <Secret label="API-ключ" k="np_api_key" bind={np.bind} hint="Кабінет НП → Налаштування → Безпека → API-ключ" />
        <Field label="Місто відправки"><NpAutocomplete kind="cities" value={np.v.np_city_name} refValue={np.v.np_city_ref} placeholder="Почніть вводити"
          onType={(t) => np.setV({ ...np.v, np_city_name: t, np_city_ref: "" })} onPick={(o) => np.setV({ ...np.v, np_city_name: o.name, np_city_ref: o.ref, np_warehouse_name: "", np_warehouse_ref: "" })} /></Field>
        <Field label="Відділення відправки"><NpAutocomplete kind="warehouses" cityRef={np.v.np_city_ref} value={np.v.np_warehouse_name} refValue={np.v.np_warehouse_ref} placeholder="Номер або адреса"
          onType={(t) => np.setV({ ...np.v, np_warehouse_name: t, np_warehouse_ref: "" })} onPick={(o) => np.setV({ ...np.v, np_warehouse_name: o.name, np_warehouse_ref: o.ref })} /></Field>
        <div className="cols">
          <Field label="Хто платить за доставку"><select {...np.bind("np_payer")}><option value="Recipient">Отримувач</option><option value="Sender">Відправник</option></select></Field>
          <Field label="Накладений платіж"><select {...np.bind("np_cod_mode")}><option value="backward">Грошовий переказ</option><option value="afterpayment">Контроль оплати</option></select></Field>
        </div>
        <div className="cols">
          <Field label="Вага за замовчуванням, кг" hint="Якщо в товарах вага не вказана"><input {...np.bind("np_default_weight")} inputMode="decimal" /></Field>
          <Field label="Розміри посилки, см" hint="Довжина × ширина × висота, напр. 20x15x10"><input {...np.bind("np_seat_size")} /></Field>
        </div>
        <Field label="Опис відправлення"><input {...np.bind("np_description")} /></Field>
        <Field label="Телефон відправника"><input {...np.bind("np_sender_phone")} /></Field>
        <p className="hint">Відправник: {s.values.np_sender_ref ? <Badge kind="ok">завантажено</Badge> : <Badge>не завантажено</Badge>} — після збереження ключа натисніть «Завантажити відправника».</p>
        <div className="form-actions"><button className="btn primary" disabled={save.isPending}>Зберегти</button>
          <button type="button" className="btn" disabled={!s.values.np_api_key} onClick={() => save.mutate({ path: "/settings/np/load-sender", method: "post" })}>Завантажити відправника</button></div>
      </form>
      <div className="stack">
        <form className="card form" onSubmit={(e) => { e.preventDefault(); save.mutate({ path: "/settings/up", body: up.v }); }}>
          <h2>Укрпошта <Badge kind="warn">бета</Badge></h2>
          <Secret label="Bearer eCom" k="up_bearer" bind={up.bind} /><Secret label="Counterparty token" k="up_token" bind={up.bind} />
          <Secret label="Bearer StatusTracking" k="up_tracking_bearer" bind={up.bind} hint="Якщо порожньо — Bearer eCom" />
          <div className="cols">
            <Field label="UUID клієнта-відправника"><input className="mono" {...up.bind("up_sender_uuid")} /></Field>
            <Field label="Тип відправлення"><select {...up.bind("up_type")}><option value="STANDARD">Стандарт</option><option value="EXPRESS">Експрес</option></select></Field>
          </div>
          <label className="check"><input type="checkbox" {...up.check("up_sandbox")} /> Тестове середовище</label>
          <div className="form-actions"><button className="btn primary">Зберегти</button></div>
        </form>
        <form className="card form" onSubmit={(e) => { e.preventDefault(); save.mutate({ path: "/settings/meest", body: me.v }); }}>
          <h2>Meest <Badge kind="warn">бета</Badge></h2>
          <div className="cols"><Field label="Логін API"><input {...me.bind("meest_username")} /></Field><Secret label="Пароль API" k="meest_password" bind={me.bind} /></div>
          <Field label="ID відділення відправника"><input className="mono" {...me.bind("meest_sender_branch_id")} /></Field>
          <div className="cols"><Field label="Відправник"><input {...me.bind("meest_sender_name")} /></Field><Field label="Телефон"><input {...me.bind("meest_sender_phone")} /></Field></div>
          <div className="form-actions"><button className="btn primary">Зберегти</button></div>
        </form>
      </div>
    </div>
  );
}

function Sms({ s }: { s: S }) {
  const save = useSave();
  const toast = useToast();
  const f = useForm(s, ["sms_enabled", "sms_token", "sms_sender", "viber_sender"]);
  const [test, setTest] = useState({ phone: "", channel: "sms" });
  const [nt, setNt] = useState({ status_id: s.statuses[0]?.id ?? 0, channel: "sms", text: "" });
  const testMut = useMutation({ mutationFn: () => api.post("/settings/sms-test", test), onSuccess: () => toast("Тестове повідомлення відправлено"), onError: (e) => toast(errText(e), "error") });
  return (
    <div className="grid half">
      <div className="stack">
        <form className="card form" onSubmit={(e) => { e.preventDefault(); save.mutate({ path: "/settings/sms", body: f.v }); }}>
          <h2>TurboSMS</h2>
          <label className="check"><input type="checkbox" {...f.check("sms_enabled")} /> Автоматично надсилати при зміні статусу</label>
          <Secret label="Токен API" k="sms_token" bind={f.bind} hint="turbosms.ua → Підключення → API (HTTP)" />
          <div className="cols"><Field label="Альфа-ім'я SMS"><input {...f.bind("sms_sender")} /></Field><Field label="Відправник Viber"><input {...f.bind("viber_sender")} /></Field></div>
          <div className="form-actions"><button className="btn primary">Зберегти</button></div>
        </form>
        <form className="card form" onSubmit={(e) => { e.preventDefault(); testMut.mutate(); }}>
          <h2>Тестове повідомлення</h2>
          <div className="cols"><Field label="Телефон"><input value={test.phone} onChange={(e) => setTest({ ...test, phone: e.target.value })} required /></Field>
            <Field label="Канал"><select value={test.channel} onChange={(e) => setTest({ ...test, channel: e.target.value })}><option value="sms">SMS</option><option value="viber">Viber</option></select></Field></div>
          <div className="form-actions"><button className="btn" disabled={testMut.isPending}>Надіслати</button></div>
        </form>
        <div className="card flush"><div style={{ padding: "14px 16px 4px" }}><h2>Останні повідомлення</h2></div>
          <table className="t dense"><tbody>{s.sms_log.map((m) => (
            <tr key={m.id}><td className="nowrap">{dt(m.created_at, true)}<span className="sub">{phone(m.phone)}</span></td><td>{m.text}{m.error && <span className="sub lowstock">{m.error}</span>}</td>
              <td><Badge kind={m.status === "sent" ? "ok" : m.status === "failed" ? "bad" : "warn"}>{m.status}</Badge></td></tr>
          ))}{!s.sms_log.length && <tr><td><Empty>Ще нічого не відправлялось</Empty></td></tr>}</tbody></table></div>
      </div>
      <div className="stack">
        <div className="card">
          <h2>Шаблони за статусами</h2>
          <p className="hint">Змінні: {Object.entries(s.placeholders).map(([k, n]) => <code key={k} title={n} style={{ marginRight: 4 }}>{k}</code>)}</p>
          {s.sms_templates.map((t) => <TemplateRow key={t.id} t={t} statuses={s.statuses} onSave={(body) => save.mutate({ path: "/settings/sms-templates", body, method: "post" })} />)}
        </div>
        <form className="card form" onSubmit={(e) => { e.preventDefault(); save.mutate({ path: "/settings/sms-templates", body: { ...nt, active: true }, method: "post" }); setNt({ ...nt, text: "" }); }}>
          <h2>Новий шаблон</h2>
          <div className="cols"><Field label="Статус"><select value={nt.status_id} onChange={(e) => setNt({ ...nt, status_id: Number(e.target.value) })}>{s.statuses.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select></Field>
            <Field label="Канал"><select value={nt.channel} onChange={(e) => setNt({ ...nt, channel: e.target.value })}><option value="sms">SMS</option><option value="viber">Viber</option><option value="hybrid">Viber → SMS</option></select></Field></div>
          <Field label="Текст"><textarea rows={3} value={nt.text} onChange={(e) => setNt({ ...nt, text: e.target.value })} required /></Field>
          <div className="form-actions"><button className="btn primary"><Plus size={14} /> Додати</button></div>
        </form>
      </div>
    </div>
  );
}

function TemplateRow({ t, statuses, onSave }: { t: S["sms_templates"][number]; statuses: Status[]; onSave: (b: Record<string, unknown>) => void }) {
  const [v, setV] = useState(t);
  return (
    <form className="form tpl" onSubmit={(e) => { e.preventDefault(); onSave(v); }}>
      <div className="row"><select value={v.status_id} onChange={(e) => setV({ ...v, status_id: Number(e.target.value) })}>{statuses.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
        <select value={v.channel} onChange={(e) => setV({ ...v, channel: e.target.value })} style={{ maxWidth: 150 }}><option value="sms">SMS</option><option value="viber">Viber</option><option value="hybrid">Viber → SMS</option></select></div>
      <textarea rows={2} value={v.text} onChange={(e) => setV({ ...v, text: e.target.value })} />
      <div className="row"><label className="check"><input type="checkbox" checked={v.active} onChange={(e) => setV({ ...v, active: e.target.checked })} /> Активний</label><span className="spacer" />
        <button type="button" className="btn sm danger" onClick={() => { if (window.confirm("Видалити шаблон?")) onSave({ id: t.id, delete: true }); }}><Trash2 size={13} /></button>
        <button className="btn sm">Зберегти</button></div>
    </form>
  );
}

function Statuses({ s }: { s: S }) {
  const save = useSave();
  const [rows, setRows] = useState(s.statuses);
  const [nw, setNw] = useState({ name: "", color: "#64748b", stock_action: "none", sort: 200 });
  const upd = (id: number, patch: Partial<Status>) => setRows(rows.map((r) => (r.id === id ? { ...r, ...patch } : r)));
  return (
    <div className="stack">
      <div className="card flush tablewrap">
        <table className="t dense">
          <thead><tr><th>Порядок</th><th>Колір</th><th>Назва</th><th>Дія зі складом</th><th title="Рахується як підтверджене у звітах">Апрув</th><th>Фінальний</th><th>Активний</th><th /></tr></thead>
          <tbody>{rows.map((r) => (
            <tr key={r.id}>
              <td style={{ width: 80 }}><input type="number" value={r.sort} onChange={(e) => upd(r.id, { sort: Number(e.target.value) })} /></td>
              <td style={{ width: 56 }}><input type="color" value={r.color} onChange={(e) => upd(r.id, { color: e.target.value })} /></td>
              <td><input value={r.name} onChange={(e) => upd(r.id, { name: e.target.value })} /><span className="sub mono">{r.code}</span></td>
              <td><select value={r.stock_action} onChange={(e) => upd(r.id, { stock_action: e.target.value })}>{Object.entries(s.stock_actions).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></td>
              <td><input type="checkbox" checked={r.approved} onChange={(e) => upd(r.id, { approved: e.target.checked })} /></td>
              <td><input type="checkbox" checked={r.final} onChange={(e) => upd(r.id, { final: e.target.checked })} /></td>
              <td><input type="checkbox" checked={r.active} disabled={r.code === "new"} onChange={(e) => upd(r.id, { active: e.target.checked })} /></td>
              <td>{!r.system && <button className="btn sm danger" onClick={() => { if (window.confirm("Видалити статус?")) save.mutate({ path: `/settings/statuses/${r.id}`, method: "del" }, { onSuccess: (x) => setRows(x.statuses) }); }}><Trash2 size={13} /></button>}</td>
            </tr>
          ))}</tbody>
        </table>
        <div style={{ padding: 12 }}><button className="btn primary" onClick={() => save.mutate({ path: "/settings/statuses", body: rows })}>Зберегти статуси</button></div>
      </div>
      <form className="card row" onSubmit={(e) => { e.preventDefault(); save.mutate({ path: "/settings/statuses", body: nw, method: "post" }, { onSuccess: (x) => { setRows(x.statuses); setNw({ ...nw, name: "" }); } }); }}>
        <Field label="Новий статус"><input value={nw.name} onChange={(e) => setNw({ ...nw, name: e.target.value })} required /></Field>
        <Field label="Колір"><input type="color" value={nw.color} onChange={(e) => setNw({ ...nw, color: e.target.value })} /></Field>
        <Field label="Дія зі складом"><select value={nw.stock_action} onChange={(e) => setNw({ ...nw, stock_action: e.target.value })}>{Object.entries(s.stock_actions).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></Field>
        <button className="btn"><Plus size={14} /> Додати</button>
      </form>
      <p className="hint"><b>Резервувати</b> — товар відкладається під замовлення. <b>Списати</b> — знімається зі складу. <b>Повернути</b> — списаний товар повертається. <b>Зняти резерв</b> — скасування до відправки. Кожна дія виконується один раз.</p>
    </div>
  );
}

function Users({ s }: { s: S }) {
  const meta = useMeta();
  const qc = useQueryClient();
  const toast = useToast();
  const [nw, setNw] = useState({ username: "", full_name: "", role: "manager", password: "" });
  const mut = useMutation({
    mutationFn: ({ id, body }: { id?: number; body: Record<string, unknown> }) => (id ? api.patch(`/users/${id}`, body) : api.post("/users", body)),
    onSuccess: (_r, vars) => { qc.invalidateQueries({ queryKey: ["settings"] }); qc.invalidateQueries({ queryKey: ["meta"] }); toast("Збережено"); if (!vars.id) setNw({ username: "", full_name: "", role: "manager", password: "" }); },
    onError: (e) => toast(errText(e), "error"),
  });
  return (
    <div className="grid two">
      <div className="card flush tablewrap"><table className="t dense">
        <thead><tr><th>Користувач</th><th>Роль</th><th>Новий пароль</th><th>Активний</th><th /></tr></thead>
        <tbody>{s.users.map((u) => <UserRow key={u.id} u={u} roles={s.roles} self={u.id === meta.user.id} onSave={(body) => mut.mutate({ id: u.id, body })} />)}</tbody>
      </table></div>
      <form className="card form" onSubmit={(e) => { e.preventDefault(); mut.mutate({ body: nw }); }}>
        <h2>Новий користувач</h2>
        <div className="cols">
          <Field label="Логін"><input value={nw.username} onChange={(e) => setNw({ ...nw, username: e.target.value })} required autoComplete="off" /></Field>
          <Field label="Ім'я"><input value={nw.full_name} onChange={(e) => setNw({ ...nw, full_name: e.target.value })} /></Field>
        </div>
        <Field label="Роль"><select value={nw.role} onChange={(e) => setNw({ ...nw, role: e.target.value })}>{Object.entries(s.roles).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></Field>
        <Field label="Пароль"><input type="password" minLength={8} value={nw.password} onChange={(e) => setNw({ ...nw, password: e.target.value })} required autoComplete="new-password" /></Field>
        <div className="form-actions"><button className="btn primary"><Plus size={14} /> Додати</button></div>
        <hr /><p className="hint"><b>Менеджер</b> — замовлення, дошка, товари (перегляд), свої звіти. <b>Склад</b> — замовлення, ТТН, склад, закупівлі. <b>Адміністратор</b> — усе.</p>
      </form>
    </div>
  );
}

function UserRow({ u, roles, self, onSave }: { u: User; roles: Record<string, string>; self: boolean; onSave: (b: Record<string, unknown>) => void }) {
  const [v, setV] = useState({ full_name: u.full_name, role: u.role as string, password: "", is_active: u.is_active });
  return (
    <tr>
      <td><input value={v.full_name} onChange={(e) => setV({ ...v, full_name: e.target.value })} placeholder="Ім'я" /><span className="sub mono">{u.username}{u.last_login_at && ` · вхід ${dt(u.last_login_at, true)}`}</span></td>
      <td><select value={v.role} onChange={(e) => setV({ ...v, role: e.target.value })} disabled={self}>{Object.entries(roles).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></td>
      <td><input type="password" value={v.password} onChange={(e) => setV({ ...v, password: e.target.value })} placeholder="не змінювати" autoComplete="new-password" /></td>
      <td><input type="checkbox" checked={v.is_active} disabled={self} onChange={(e) => setV({ ...v, is_active: e.target.checked })} /></td>
      <td><button className="btn sm" onClick={() => { onSave({ ...v, password: v.password || undefined }); setV({ ...v, password: "" }); }}>Зберегти</button></td>
    </tr>
  );
}
