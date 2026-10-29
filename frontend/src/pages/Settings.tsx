import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Building2, Copy, Plus, RefreshCw, Settings as SettingsIcon, Star, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import { errText, useMeta, useToast } from "../lib/app";
import { dt, phone } from "../lib/format";
import type { BlockedIp, Cashier, CustomerGroup, DirItem, LegalEntity, NpAccount, PaymentMethod, Reason, Settings, Shop, ShopCheck, ShopSync, Status, User } from "../lib/types";
import { PAY_ICONS, PayIcon } from "../components/payicons";
import { MarkLookPick } from "../components/marks";
import { Badge, Empty, Field, NpAutocomplete, Spinner } from "../components/ui";

type S = Settings;
const TABS = { general: "Загальні", entities: "Юрособи", dirs: "Довідники", statuses: "Статуси", checkbox: "Checkbox", delivery: "Доставка", market: "Маркетплейси",
  webhook: "Прийом заявок", sms: "SMS / Viber", customers: "Покупці", users: "Користувачі" };

export default function SettingsPage() {
  const [tab, setTab] = useState<keyof typeof TABS>(() => (localStorage.getItem("crm-settings-tab") as keyof typeof TABS) || "general");
  const { data } = useQuery({ queryKey: ["settings"], queryFn: () => api.get<S>("/settings") });
  const choose = (t: keyof typeof TABS) => { setTab(t); localStorage.setItem("crm-settings-tab", t); };
  return (
    <div>
      <div className="head"><h1><span className="h-ico"><SettingsIcon size={18} /></span>Налаштування</h1></div>
      <nav className="subnav">{Object.entries(TABS).map(([k, n]) => <a key={k} className={tab === k ? "on" : ""} onClick={() => choose(k as keyof typeof TABS)}>{n}</a>)}</nav>
      {!data ? <Empty><Spinner /></Empty> : <>
        {tab === "general" && <General s={data} />}
        {tab === "entities" && <LegalEntities s={data} />}
        {tab === "customers" && <CustomerSettings />}
        {tab === "dirs" && <Directories s={data} />}
        {tab === "market" && <Shops s={data} />}
        {tab === "checkbox" && <CheckboxSettings s={data} />}
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
        <pre className="code wrap">{url}</pre>
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
  const up = useForm(s, ["up_bearer", "up_token", "up_tracking_bearer", "up_sender_uuid", "up_sandbox", "up_type"]);
  const me = useForm(s, ["meest_username", "meest_password", "meest_sender_branch_id", "meest_sender_name", "meest_sender_phone"]);
  return (
    <div className="stack">
      <NpAccounts s={s} />
      <div className="grid half">
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
          <thead><tr><th>Порядок</th><th>Колір</th><th>Назва</th><th title="У якому розділі показується замовлення з цим статусом">Розділ</th><th>Дія зі складом</th><th title="Рахується як підтверджене у звітах">Апрув</th><th>Фінальний</th><th>Активний</th><th /></tr></thead>
          <tbody>{rows.map((r) => (
            <tr key={r.id}>
              <td style={{ width: 80 }}><input type="number" value={r.sort} onChange={(e) => upd(r.id, { sort: Number(e.target.value) })} /></td>
              <td style={{ width: 56 }}><input type="color" value={r.color} onChange={(e) => upd(r.id, { color: e.target.value })} /></td>
              <td><input value={r.name} onChange={(e) => upd(r.id, { name: e.target.value })} /><span className="sub mono">{r.code}</span></td>
              <td><select value={r.stage ?? "order"} onChange={(e) => upd(r.id, { stage: e.target.value as Status["stage"] })}><option value="lead">Ліди</option><option value="order">Замовлення</option></select></td>
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
      <p className="hint"><b>Розділ</b>: «Ліди» — обробка заявки (новий, недозвон, передзвонити…), «Замовлення» — усе після підтвердження. Зміна статусу переносить замовлення між розділами.</p>
      <p className="hint"><b>Резервувати</b> — товар відкладається під замовлення. <b>Списати</b> — знімається зі складу. <b>Повернути</b> — списаний товар повертається. <b>Зняти резерв</b> — скасування до відправки. Кожна дія виконується один раз.</p>
    </div>
  );
}

function Users({ s }: { s: S }) {
  const meta = useMeta();
  const qc = useQueryClient();
  const toast = useToast();
  const [nw, setNw] = useState({ username: "", full_name: "", role: "manager", password: "", offices: [] as number[] });
  const mut = useMutation({
    mutationFn: ({ id, body }: { id?: number; body: Record<string, unknown> }) => (id ? api.patch(`/users/${id}`, body) : api.post("/users", body)),
    onSuccess: (_r, vars) => { qc.invalidateQueries({ queryKey: ["settings"] }); qc.invalidateQueries({ queryKey: ["meta"] }); toast("Збережено"); if (!vars.id) setNw({ username: "", full_name: "", role: "manager", password: "", offices: [] }); },
    onError: (e) => toast(errText(e), "error"),
  });
  return (
    <div className="grid two">
      <div className="card flush tablewrap"><table className="t dense">
        <thead><tr><th>Користувач</th><th>Роль</th>{s.offices.length > 0 && <th title="Замовлення яких відділів бачить користувач">Відділи</th>}<th>Новий пароль</th><th>Активний</th><th /></tr></thead>
        <tbody>{s.users.map((u) => <UserRow key={u.id} u={u} roles={s.roles} offices={s.offices.filter((o) => o.active)} self={u.id === meta.user.id} onSave={(body) => mut.mutate({ id: u.id, body })} />)}</tbody>
      </table></div>
      <form className="card form" onSubmit={(e) => { e.preventDefault(); mut.mutate({ body: nw }); }}>
        <h2>Новий користувач</h2>
        <div className="cols">
          <Field label="Логін"><input value={nw.username} onChange={(e) => setNw({ ...nw, username: e.target.value })} required autoComplete="off" /></Field>
          <Field label="Ім'я"><input value={nw.full_name} onChange={(e) => setNw({ ...nw, full_name: e.target.value })} /></Field>
        </div>
        <Field label="Роль"><select value={nw.role} onChange={(e) => setNw({ ...nw, role: e.target.value })}>{Object.entries(s.roles).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></Field>
        {s.offices.some((o) => o.active) && <Field label="Відділи" hint="Порожньо — бачить замовлення всіх відділів"><OfficeChips offices={s.offices.filter((o) => o.active)} value={nw.offices} onChange={(v) => setNw({ ...nw, offices: v })} /></Field>}
        <Field label="Пароль"><input type="password" minLength={8} value={nw.password} onChange={(e) => setNw({ ...nw, password: e.target.value })} required autoComplete="new-password" /></Field>
        <div className="form-actions"><button className="btn primary"><Plus size={14} /> Додати</button></div>
        <hr /><p className="hint"><b>Менеджер</b> — замовлення, дошка, товари (перегляд), свої звіти. <b>Склад</b> — замовлення, ТТН, склад, закупівлі. <b>Адміністратор</b> — усе.</p>
      </form>
    </div>
  );
}

function OfficeChips({ offices, value, onChange }: { offices: DirItem[]; value: number[]; onChange: (v: number[]) => void }) {
  return <div className="chips">{offices.map((o) => {
    const on = value.includes(o.id);
    return <button type="button" key={o.id} className={`chip ${on ? "on" : ""}`} onClick={() => onChange(on ? value.filter((x) => x !== o.id) : [...value, o.id])}>{o.name}</button>;
  })}</div>;
}

function UserRow({ u, roles, offices, self, onSave }: { u: User; roles: Record<string, string>; offices: DirItem[]; self: boolean; onSave: (b: Record<string, unknown>) => void }) {
  const [v, setV] = useState({ full_name: u.full_name, role: u.role as string, password: "", is_active: u.is_active, offices: u.offices ?? [] });
  return (
    <tr>
      <td><input value={v.full_name} onChange={(e) => setV({ ...v, full_name: e.target.value })} placeholder="Ім'я" /><span className="sub mono">{u.username}{u.last_login_at && ` · вхід ${dt(u.last_login_at, true)}`}</span></td>
      <td><select value={v.role} onChange={(e) => setV({ ...v, role: e.target.value })} disabled={self}>{Object.entries(roles).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></td>
      {offices.length > 0 && <td>{v.role === "admin" ? <span className="muted">усі</span> : <OfficeChips offices={offices} value={v.offices} onChange={(o) => setV({ ...v, offices: o })} />}</td>}
      <td><input type="password" value={v.password} onChange={(e) => setV({ ...v, password: e.target.value })} placeholder="не змінювати" autoComplete="new-password" /></td>
      <td><input type="checkbox" checked={v.is_active} disabled={self} onChange={(e) => setV({ ...v, is_active: e.target.checked })} /></td>
      <td><button className="btn sm" onClick={() => { onSave({ ...v, password: v.password || undefined }); setV({ ...v, password: "" }); }}>Зберегти</button></td>
    </tr>
  );
}

// ---------------------------------------------------------------- довідники
function Directories({ s }: { s: S }) {
  return (
    <div className="stack">
      <PaymentMethods s={s} />
      <div className="grid half">
        <DirEditor kind="offices" title="Відділи" hint="Відділ — це група джерел (наприклад «Маркетплейси» = Rozetka + Prom). Відділ замовлення визначається його джерелом. Менеджеру можна відкрити лише свої відділи (Користувачі)." items={s.offices} />
        <DirEditor kind="sources" title="Джерела замовлень" hint="Додаються лише тут; у замовленні джерело вибирають зі списку. Кожному джерелу вкажіть відділ." items={s.order_sources} offices={s.offices} />
      </div>
      <div className="grid half">
        <DirEditor kind="reasons" title="Причини (атрибути статусів)" hint="Менеджер обирає причину, коли ставить статус. Позначте, для яких статусів кожна причина." items={s.reasons} statuses={s.statuses} />
        <div className="stack">
          <DirEditor kind="marks" title="Позначки" hint="Швидкі позначки замовлення з нагадуванням: «Терміново», «Покласти чек»…" items={s.marks} />
          <ExtraFields s={s} />
        </div>
      </div>
    </div>
  );
}

function ExtraFields({ s }: { s: S }) {
  const save = useSave();
  const { v, bind, check } = useForm(s, ["extra1_name", "extra2_name", "extra3_name", "extra4_name", "extra1_on", "extra2_on", "extra3_on", "extra4_on"]);
  return (
    <form className="card form" onSubmit={(e) => { e.preventDefault(); save.mutate({ path: "/settings/fields", body: v }); }}>
      <h2>Додаткові поля замовлення</h2>
      <p className="hint">До чотирьох довільних полів у картці (магазин маркетплейсу, номер замовлення Rozetka, посилання…). Вимкнені поля не показуються в картці й фільтрах; дані в них зберігаються. З лендингу — як extra1–extra4.</p>
      <div className="xf-list">{[1, 2, 3, 4].map((i) => (
        <div className={`xf-row ${v[`extra${i}_on`] === "0" ? "off" : ""}`} key={i}>
          <label className="switch" title={v[`extra${i}_on`] === "0" ? "Поле вимкнено" : "Поле показується"}><input type="checkbox" {...check(`extra${i}_on`)} /><span /></label>
          <span className="xf-n">Поле {i}</span>
          <input {...bind(`extra${i}_name`)} placeholder={`Назва поля ${i}`} disabled={v[`extra${i}_on`] === "0"} aria-label={`Назва поля ${i}`} />
        </div>
      ))}</div>
      <div className="form-actions"><button className="btn primary" disabled={save.isPending}>Зберегти</button></div>
    </form>
  );
}

type Row<T> = T & { key: string; delete?: boolean };
let rowSeq = 0;
const rk = () => `r${++rowSeq}`;

function DirEditor({ kind, title, hint, items, statuses, offices }: { kind: string; title: string; hint: string; items: (DirItem | Reason)[]; statuses?: Status[]; offices?: DirItem[] }) {
  const save = useSave();
  const [rows, setRows] = useState<Row<DirItem & { status_ids?: number[] }>[]>(() => items.map((x) => ({ ...x, key: rk() })));
  const upd = (key: string, patch: Partial<DirItem & { status_ids?: number[]; delete?: boolean }>) => setRows(rows.map((r) => (r.key === key ? { ...r, ...patch } : r)));
  const visible = rows.filter((r) => !r.delete);
  const [open, setOpen] = useState("");
  const submit = () => save.mutate({ path: `/settings/dir/${kind}`, method: "put", body: rows.filter((r) => r.name.trim()).map((r, i) => ({ id: r.id || undefined, name: r.name, active: r.active, sort: i * 10, delete: !!r.delete, status_ids: r.status_ids, office_id: offices ? r.office_id ?? null : undefined,
    ...(kind === "marks" ? { icon: r.icon ?? "tag", color: r.color ?? "#475569" } : {}) })) },
    { onSuccess: (x) => { const list = (x as S)[kind === "sources" ? "order_sources" : (kind as "offices" | "reasons" | "marks")] as (DirItem | Reason)[]; setRows(list.map((y) => ({ ...y, key: rk() }))); } });
  return (
    <div className="card">
      <h2>{title} <span className="muted">{visible.length}</span></h2>
      <p className="hint">{hint}</p>
      <div className="dir-list">
        {visible.map((r) => (
          <div className={`dir-row ${r.active ? "" : "off"}`} key={r.key}>
            {kind === "marks" && <MarkLookPick icon={r.icon} color={r.color} onChange={(icon, color) => upd(r.key, { icon, color })} />}
            <input value={r.name} onChange={(e) => upd(r.key, { name: e.target.value })} placeholder="Назва" />
            {offices && <select className="dir-office" value={r.office_id ?? ""} title="Відділ джерела" onChange={(e) => upd(r.key, { office_id: e.target.value ? Number(e.target.value) : null })}>
              <option value="">без відділу</option>{offices.filter((o) => o.active).map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</select>}
            <label className="mini-check" title="Показувати в замовленнях"><input type="checkbox" checked={r.active} onChange={(e) => upd(r.key, { active: e.target.checked })} /> активна</label>
            <button type="button" className="x" title="Прибрати" onClick={() => (r.id ? upd(r.key, { delete: true }) : setRows(rows.filter((x) => x.key !== r.key)))}>×</button>
            {statuses && open !== r.key && <button type="button" className="dir-st-btn" onClick={() => setOpen(r.key)}>
              Для статусів: {(r.status_ids ?? []).map((i) => statuses.find((st) => st.id === i)?.name).filter(Boolean).join(", ") || "не вибрано"} · змінити</button>}
            {statuses && open === r.key && <div className="chips dir-statuses">{statuses.filter((st) => st.active).map((st) => {
              const on = (r.status_ids ?? []).includes(st.id);
              return <button type="button" key={st.id} className={`chip ${on ? "on" : ""}`} onClick={() => upd(r.key, { status_ids: on ? (r.status_ids ?? []).filter((i) => i !== st.id) : [...(r.status_ids ?? []), st.id] })}>{st.name}</button>;
            })}</div>}
          </div>
        ))}
      </div>
      <div className="form-actions">
        <button type="button" className="btn sm" onClick={() => setRows([...rows, { id: 0, name: "", active: true, sort: 0, status_ids: [], key: rk() }])}><Plus size={14} /> Додати</button>
        <span className="spacer" />
        <button type="button" className="btn primary" disabled={save.isPending} onClick={submit}>Зберегти</button>
      </div>
    </div>
  );
}

function PaymentMethods({ s }: { s: S }) {
  const save = useSave();
  const [rows, setRows] = useState<Row<PaymentMethod>[]>(() => s.payment_methods.map((m) => ({ ...m, key: rk() })));
  const [showOff, setShowOff] = useState(false);
  const upd = (key: string, patch: Partial<PaymentMethod>) => setRows(rows.map((r) => (r.key === key ? { ...r, ...patch } : r)));
  const move = (i: number, d: number) => { const a = [...rows]; const j = i + d; if (j < 0 || j >= a.length) return; [a[i], a[j]] = [a[j], a[i]]; setRows(a); };
  const submit = () => save.mutate({ path: "/settings/payment-methods", method: "put", body: rows.filter((r) => r.name.trim()).map((r, i) => ({ id: r.id || undefined, name: r.name, icon: r.icon, kind: r.kind, checkbox_type: r.checkbox_type, np_cod: r.np_cod ?? "", active: r.active, sort: i * 10 })) },
    { onSuccess: (x) => setRows((x as S).payment_methods.map((m) => ({ ...m, key: rk() }))) });
  const shown = rows.map((r, i) => [r, i] as const).filter(([r]) => showOff || r.active);
  return (
    <div className="card flush">
      <div className="card-head pad"><div><h2>Види оплат <span className="muted">{rows.filter((r) => r.active).length} з {rows.length}</span></h2>
        <p className="hint">Вид оплати визначає розрахунок, тип оплати в чеку Checkbox і що має стояти в ТТН Нової Пошти (колонка «Перевірка оплати» в замовленнях). Номери (ID) такі ж, як у LP-CRM.</p></div>
        <label className="mini-check"><input type="checkbox" checked={showOff} onChange={(e) => setShowOff(e.target.checked)} /> показати вимкнені</label></div>
      <div className="tablewrap"><table className="t dense pm-table">
        <thead><tr><th>ID</th><th>Значок</th><th>Назва</th><th>Розрахунок</th><th title="Тип оплати в чеку Checkbox">Checkbox</th><th title="Що має стояти в ТТН Нової Пошти — для колонки «Перевірка оплати»">ТТН Нової Пошти</th><th>Активний</th><th /></tr></thead>
        <tbody>{shown.map(([r, i]) => (
          <tr key={r.key} className={r.active ? "" : "off"}>
            <td className="muted mono">{r.id || "нов."}</td>
            <td><div className="pm-icon"><PayIcon icon={r.icon} size={24} />
              <select value={r.icon} onChange={(e) => upd(r.key, { icon: e.target.value })} aria-label="Значок">{Object.entries(PAY_ICONS).map(([k, d]) => <option key={k} value={k}>{d.label}</option>)}</select></div></td>
            <td><input value={r.name} onChange={(e) => upd(r.key, { name: e.target.value })} /></td>
            <td><select value={r.kind} onChange={(e) => upd(r.key, { kind: e.target.value as PaymentMethod["kind"] })}>
              <option value="cod">Післяплата</option><option value="partial">Передоплата + післяплата</option><option value="prepaid">Оплачено (ТТН без післяплати)</option></select></td>
            <td><select value={r.checkbox_type} onChange={(e) => upd(r.key, { checkbox_type: e.target.value })}>
              <option value="">— не фіскалізувати</option>{Object.entries(s.checkbox_payments).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></td>
            <td><select value={r.kind === "prepaid" ? "none" : r.np_cod ?? ""} disabled={r.kind === "prepaid"} title={r.kind === "prepaid" ? "Оплачено повністю — у ТТН не має бути післяплати" : undefined}
              onChange={(e) => upd(r.key, { np_cod: e.target.value as PaymentMethod["np_cod"] })}>
              <option value="">— не перевіряти</option><option value="control">Контроль оплати</option><option value="backward">Грошовий переказ</option><option value="none">Без післяплати</option></select></td>
            <td><input type="checkbox" checked={r.active} onChange={(e) => upd(r.key, { active: e.target.checked })} /></td>
            <td className="nowrap"><button type="button" className="x" title="Вище" onClick={() => move(i, -1)}><ArrowUp size={13} /></button><button type="button" className="x" title="Нижче" onClick={() => move(i, 1)}><ArrowDown size={13} /></button></td>
          </tr>
        ))}</tbody>
      </table></div>
      <div className="form-actions pad">
        <button type="button" className="btn sm" onClick={() => { setShowOff(true); setRows([...rows, { id: 0, name: "", icon: "cash", kind: "cod", checkbox_type: "", np_cod: "", active: true, sort: 0, key: rk() }]); }}><Plus size={14} /> Додати вид оплати</button>
        <span className="spacer" />
        <button type="button" className="btn primary" disabled={save.isPending} onClick={submit}>Зберегти види оплат</button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------- Нова Пошта: ключі й правила статусів
const NP_PAYERS = { Recipient: "Одержувач", Sender: "Відправник", ThirdPerson: "Третя особа" };
const NP_CARGO = { Parcel: "Посилка", Cargo: "Вантаж", Documents: "Документи", TiresWheels: "Шини-диски", Pallet: "Палети" };
const NP_SERVICE = { WarehouseWarehouse: "Відділення → відділення", WarehouseDoors: "Відділення → адреса", DoorsWarehouse: "Адреса → відділення", DoorsDoors: "Адреса → адреса" };
type Acc = NpAccount & { key: string; delete?: boolean };
type Sender = { ref: string; name: string; contacts: { ref: string; name: string; phone: string }[] };

function NpAccounts({ s }: { s: S }) {
  const save = useSave();
  const [rows, setRows] = useState<Acc[]>(() => s.np_accounts.map((a) => ({ ...a, key: rk() })));
  const [open, setOpen] = useState<string>(() => (s.np_accounts.length === 1 ? "" : ""));
  const reset = (x: S) => setRows(x.np_accounts.map((a) => ({ ...a, key: rk() })));
  const upd = (key: string, patch: Partial<Acc>) => setRows(rows.map((r) => (r.key === key ? { ...r, ...patch } : r)));
  const body = () => rows.map((r) => ({ ...r, key: undefined, id: r.id || undefined }));
  const submit = () => save.mutate({ path: "/settings/np-accounts", method: "put", body: body() }, { onSuccess: (x) => reset(x as S) });
  const sync = (id: number) => save.mutate({ path: `/settings/np-accounts/${id}/sync`, method: "post" }, { onSuccess: (x) => reset(x as S) });
  const visible = rows.filter((r) => !r.delete);
  const blank = (): Acc => ({ id: 0, name: "", api_key: "", sender_ref: "", sender_name: "", contact_ref: "", contact_name: "", sender_phone: "",
    city_name: "", city_ref: "", warehouse_name: "", warehouse_ref: "", payer: "Recipient", cargo_type: "Parcel", service_type: "WarehouseWarehouse",
    cod_mode: "backward", cod_payer: "Recipient", info_comment: false, info_items: true, info_item_ids: false, default_weight: 0.5, seat_size: "20x15x10",
    description: "Товар", office_id: null, legal_entity_id: null, is_default: rows.length === 0, is_active: true, directory: {}, key: rk() });
  return (
    <div className="stack">
      <div className="card">
        <div className="card-head"><h2>Нова Пошта — ключі API <span className="muted">{visible.length}</span></h2>
          <button type="button" className="btn sm" onClick={() => { const b = blank(); setRows([...rows, b]); setOpen(b.key); }}><Plus size={14} /> Додати ключ</button></div>
        <p className="hint">Ключ кожного ФОП зі своїми параметрами ТТН. Для замовлення береться ключ, вибраний у картці, інакше — закріплений за відділом, інакше — основний.</p>
        {visible.length === 0 && <Empty>Ключів ще немає — додайте ключ з кабінету НП (Налаштування → Безпека → API-ключ)</Empty>}
        <div className="np-accs">
          {visible.map((a) => {
            const senders = ((a.directory as { senders?: Sender[] })?.senders ?? []);
            const sender = senders.find((x) => x.ref === a.sender_ref);
            const isOpen = open === a.key;
            return (
              <div className={`np-acc ${isOpen ? "open" : ""}`} key={a.key}>
                <button type="button" className="np-acc-h" onClick={() => setOpen(isOpen ? "" : a.key)}>
                  <b>{a.name || "Новий ключ"}</b>{a.is_default && <Badge kind="info">основний</Badge>}{!a.is_active && <Badge>вимкнено</Badge>}
                  <span className="muted">{[a.contact_name, a.city_name, a.warehouse_name].filter(Boolean).join(" · ") || (a.api_key ? "ключ збережено — синхронізуйте відправника" : "без ключа")}</span>
                </button>
                {isOpen && (
                  <div className="form np-acc-b">
                    <div className="cols">
                      <Field label="Назва" hint="Як показувати менеджерам, напр. «ФОП Максимчук О.В.»"><input value={a.name} onChange={(e) => upd(a.key, { name: e.target.value })} /></Field>
                      <Field label="API-ключ" hint="Кабінет НП → Налаштування → Безпека"><input className="mono" autoComplete="off" placeholder="не вказано" value={a.api_key} onChange={(e) => upd(a.key, { api_key: e.target.value })} /></Field>
                    </div>
                    <div className="np-sync">
                      <button type="button" className="btn sm" disabled={!a.id || save.isPending} onClick={() => sync(a.id)} title={a.id ? "" : "Спершу збережіть ключ"}><RefreshCw size={14} /> Синхронізувати з кабінетом</button>
                      <span className="hint">{a.id ? "Підтягне контрагентів і контактних осіб відправника" : "Збережіть ключ, потім синхронізуйте"}</span>
                    </div>
                    {senders.length > 0 && <div className="cols">
                      <Field label="Контрагент"><select value={a.sender_ref} onChange={(e) => { const x = senders.find((y) => y.ref === e.target.value); upd(a.key, { sender_ref: e.target.value, sender_name: x?.name ?? "", contact_ref: "", contact_name: "", sender_phone: "" }); }}>
                        {senders.map((x) => <option key={x.ref} value={x.ref}>{x.name}</option>)}</select></Field>
                      <Field label="Відправник (контактна особа)"><select value={a.contact_ref} onChange={(e) => { const c = sender?.contacts.find((y) => y.ref === e.target.value); upd(a.key, { contact_ref: e.target.value, contact_name: c?.name ?? "", sender_phone: c?.phone ?? "" }); }}>
                        <option value="">оберіть</option>{(sender?.contacts ?? []).map((c) => <option key={c.ref} value={c.ref}>{c.name} ({c.phone})</option>)}</select></Field>
                    </div>}
                    <div className="cols">
                      <Field label="Місто відправки"><NpAutocomplete kind="cities" value={a.city_name} refValue={a.city_ref} placeholder="Почніть вводити"
                        onType={(t) => upd(a.key, { city_name: t, city_ref: "" })} onPick={(o) => upd(a.key, { city_name: o.name, city_ref: o.ref, warehouse_name: "", warehouse_ref: "" })} /></Field>
                      <Field label="Відділення відправки"><NpAutocomplete kind="warehouses" cityRef={a.city_ref} value={a.warehouse_name} refValue={a.warehouse_ref} placeholder="Номер або адреса"
                        onType={(t) => upd(a.key, { warehouse_name: t, warehouse_ref: "" })} onPick={(o) => upd(a.key, { warehouse_name: o.name, warehouse_ref: o.ref })} /></Field>
                    </div>
                    <div className="cols c3">
                      <Field label="Платник доставки"><select value={a.payer} onChange={(e) => upd(a.key, { payer: e.target.value })}>{Object.entries(NP_PAYERS).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></Field>
                      <Field label="Тип відправлення"><select value={a.cargo_type} onChange={(e) => upd(a.key, { cargo_type: e.target.value })}>{Object.entries(NP_CARGO).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></Field>
                      <Field label="Технологія"><select value={a.service_type} onChange={(e) => upd(a.key, { service_type: e.target.value })}>{Object.entries(NP_SERVICE).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></Field>
                    </div>
                    <div className="cols c3">
                      <Field label="Післяплата" hint="Контроль оплати — гроші на рахунок, потрібен договір з НП"><select value={a.cod_mode} onChange={(e) => upd(a.key, { cod_mode: e.target.value })}>
                        <option value="backward">Грошовий переказ</option><option value="afterpayment">Контроль оплати</option></select></Field>
                      <Field label="Платник переказу"><select value={a.cod_payer} onChange={(e) => upd(a.key, { cod_payer: e.target.value })}><option value="Recipient">Одержувач</option><option value="Sender">Відправник</option></select></Field>
                      {s.legal_entities.length > 0 ? (
                        <Field label="Юрособа" hint="Замовлення цієї юрособи йдуть з цього ключа"><select value={a.legal_entity_id ?? ""} onChange={(e) => upd(a.key, { legal_entity_id: e.target.value ? Number(e.target.value) : null })}>
                          <option value="">будь-яка</option>{s.legal_entities.filter((x) => x.is_active).map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select></Field>
                      ) : (
                        <Field label="Відділ" hint="Замовлення цього відділу йдуть з цього ключа"><select value={a.office_id ?? ""} onChange={(e) => upd(a.key, { office_id: e.target.value ? Number(e.target.value) : null })}>
                          <option value="">будь-який</option>{s.offices.filter((o) => o.active).map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</select></Field>
                      )}
                    </div>
                    <div className="cols c3">
                      <Field label="Вага за замовчуванням, кг" hint="Якщо в товарах не вказана"><input value={String(a.default_weight)} inputMode="decimal" onChange={(e) => upd(a.key, { default_weight: Number(e.target.value.replace(",", ".")) || 0 })} /></Field>
                      <Field label="Розміри за замовчуванням, см" hint="Д × Ш × В, якщо в товарах не вказані"><input value={a.seat_size} onChange={(e) => upd(a.key, { seat_size: e.target.value })} /></Field>
                      <Field label="Опис відправлення" hint="Якщо в товарах не вказаний"><input value={a.description} onChange={(e) => upd(a.key, { description: e.target.value })} /></Field>
                    </div>
                    <div><span className="lbl">Додаткова інформація на ТТН</span>
                      <div className="checks np-info">
                        <label className="check"><input type="checkbox" checked={a.info_items} onChange={(e) => upd(a.key, { info_items: e.target.checked })} /> Список товарів</label>
                        <label className="check"><input type="checkbox" checked={a.info_item_ids} onChange={(e) => upd(a.key, { info_item_ids: e.target.checked })} /> Номери товарів</label>
                        <label className="check"><input type="checkbox" checked={a.info_comment} onChange={(e) => upd(a.key, { info_comment: e.target.checked })} /> Коментар замовлення</label>
                      </div></div>
                    <div className="form-actions">
                      <label className="check"><input type="radio" name="np-default" checked={a.is_default} onChange={() => setRows(rows.map((r) => ({ ...r, is_default: r.key === a.key })))} /> Основний ключ</label>
                      <label className="check"><input type="checkbox" checked={a.is_active} onChange={(e) => upd(a.key, { is_active: e.target.checked })} /> Активний</label>
                      <span className="spacer" />
                      <button type="button" className="btn sm danger" onClick={() => { if (window.confirm("Прибрати ключ із CRM? ТТН у кабінеті НП не зміняться.")) { if (a.id) upd(a.key, { delete: true }); else setRows(rows.filter((r) => r.key !== a.key)); } }}><Trash2 size={13} /> Прибрати</button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
        {rows.length > 0 && <div className="form-actions mt"><button type="button" className="btn primary" disabled={save.isPending} onClick={submit}>Зберегти ключі</button></div>}
      </div>
      <NpRules s={s} />
    </div>
  );
}

function NpRules({ s }: { s: S }) {
  const save = useSave();
  type R = { key: string; np_code: string; status_id: number; except_ids: number[] };
  const [rows, setRows] = useState<R[]>(() => s.np_status_rules.map((r) => ({ ...r, key: rk() })));
  const [open, setOpen] = useState("");
  const statuses = s.statuses.filter((x) => x.active);
  const upd = (key: string, patch: Partial<R>) => setRows(rows.map((r) => (r.key === key ? { ...r, ...patch } : r)));
  return (
    <div className="card">
      <div className="card-head"><h2>Автоматична зміна статусів за ТТН</h2>
        <button type="button" className="btn sm" onClick={() => setRows([...rows, { key: rk(), np_code: "7", status_id: statuses[0]?.id ?? 0, except_ids: [] }])}><Plus size={14} /> Додати правило</button></div>
      <p className="hint">Коли статус ТТН Нової Пошти змінюється, замовлення переходить у вказаний статус — крім замовлень у статусах-винятках. {rows.length ? "" : "Поки правил немає, діє стандартна логіка: «в дорозі» → Відправлено, «отримано» → Отримано, «відмова» → Відмова."}</p>
      {rows.length > 0 && <div className="np-rules">
        <div className="np-rule head"><span>Статус ТТН</span><span /><span>Статус замовлення</span><span>Винятки</span><span /></div>
        {rows.map((r) => (
          <div className="np-rule" key={r.key}>
            <select value={r.np_code} onChange={(e) => upd(r.key, { np_code: e.target.value })}>{Object.entries(s.np_statuses).map(([c, n]) => <option key={c} value={c}>{n}</option>)}</select>
            <span className="muted">→</span>
            <select value={r.status_id} onChange={(e) => upd(r.key, { status_id: Number(e.target.value) })}>{statuses.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
            <button type="button" className="dir-st-btn" onClick={() => setOpen(open === r.key ? "" : r.key)}>{r.except_ids.length ? r.except_ids.map((i) => s.statuses.find((x) => x.id === i)?.name).filter(Boolean).join(", ") : "без винятків"}</button>
            <button type="button" className="x" title="Прибрати" onClick={() => setRows(rows.filter((x) => x.key !== r.key))}>×</button>
            {open === r.key && <div className="chips np-rule-ex">{statuses.map((x) => {
              const on = r.except_ids.includes(x.id);
              return <button type="button" key={x.id} className={`chip ${on ? "on" : ""}`} onClick={() => upd(r.key, { except_ids: on ? r.except_ids.filter((i) => i !== x.id) : [...r.except_ids, x.id] })}>{x.name}</button>;
            })}</div>}
          </div>
        ))}
      </div>}
      <div className="form-actions mt"><button type="button" className="btn primary" disabled={save.isPending}
        onClick={() => save.mutate({ path: "/settings/np-rules", method: "put", body: rows.map(({ key: _k, ...r }) => r) }, { onSuccess: (x) => setRows((x as S).np_status_rules.map((r) => ({ ...r, key: rk() }))) })}>Зберегти правила</button></div>
    </div>
  );
}

// ---------------------------------------------------------------- маркетплейси
const PROM_ST: Record<string, string> = { pending: "Новий / в обробці", received: "Прийнятий", delivered: "Виконаний", canceled: "Скасований", paid: "Оплачений" };
type ShopRow = Shop & { key: string; delete?: boolean };

function Shops({ s }: { s: S }) {
  const meta = useMeta();
  const save = useSave();
  const toast = useToast();
  const [rows, setRows] = useState<ShopRow[]>(() => s.shops.map((x) => ({ ...x, key: rk() })));
  const [open, setOpen] = useState("");
  const [result, setResult] = useState<Record<number, { check?: ShopCheck; sync?: ShopSync }>>({});
  const reset = (x: S) => setRows(x.shops.map((y) => ({ ...y, key: rk() })));
  const upd = (key: string, patch: Partial<ShopRow>) => setRows(rows.map((r) => (r.key === key ? { ...r, ...patch } : r)));
  const submit = () => save.mutate({ path: "/settings/shops", method: "put", body: rows.map(({ key: _k, directory: _d, last_sync_at: _l, last_error: _e, imported: _i, ...r }) => ({ ...r, id: r.id || undefined, since: r.since ? r.since.slice(0, 10) : null })) },
    { onSuccess: (x) => reset(x as S) });
  const run = async (id: number, what: "check" | "sync") => {
    try {
      const res = await api.post<ShopCheck | ShopSync>(`/settings/shops/${id}/${what}`);
      setResult((r) => ({ ...r, [id]: { ...r[id], [what]: res } }));
      const fresh = await api.get<S>("/settings");
      reset(fresh);
      toast(what === "check" ? "Підключення працює" : `Синхронізовано: нових ${(res as ShopSync).new}`);
    } catch (e) { toast(errText(e), "error"); }
  };
  const add = (kind: "rozetka" | "prom") => {
    const r: ShopRow = { id: 0, kind, name: "", login: "", secret: "", office_id: null, source_id: null, import_status_id: null, extra_field: 1,
      status_map: {}, payment_map: {}, delivery_map: {}, directory: {}, since: null, last_sync_at: null, last_error: "", imported: 0, is_active: true, key: rk() };
    setRows([...rows, r]); setOpen(r.key);
  };
  const statuses = s.statuses.filter((x) => x.active);
  const visible = rows.filter((r) => !r.delete);
  return (
    <div className="card">
      <div className="card-head"><h2>Маркетплейси <span className="muted">{visible.length}</span></h2>
        <div className="row"><button type="button" className="btn sm" onClick={() => add("rozetka")}><Plus size={14} /> Rozetka</button>
          <button type="button" className="btn sm" onClick={() => add("prom")}><Plus size={14} /> Prom</button></div></div>
      <p className="hint">Замовлення з маркетплейсів підтягуються самі кожні 5 хвилин, разом із ТТН, яку створив маркетплейс (тож дубля ТТН не буде). Коли в CRM змінюється статус, він передається назад за таблицею відповідностей.</p>
      {visible.length === 0 && <Empty>Підключіть магазин Rozetka або Prom</Empty>}
      <div className="np-accs">
        {visible.map((x) => {
          const isOpen = open === x.key;
          const dir = (x.directory ?? {}) as { statuses?: Record<string, string>; payments?: string[]; deliveries?: string[] };
          const mpStatuses = x.kind === "prom" ? PROM_ST : (dir.statuses ?? {});
          const res = x.id ? result[x.id] : undefined;
          return (
            <div className={`np-acc ${isOpen ? "open" : ""}`} key={x.key}>
              <button type="button" className="np-acc-h" onClick={() => setOpen(isOpen ? "" : x.key)}>
                <b>{x.kind === "rozetka" ? "Rozetka" : "Prom"}{x.name ? ` · ${x.name}` : ""}</b>{!x.is_active && <Badge>вимкнено</Badge>}
                {x.last_error ? <Badge kind="bad" title={x.last_error}>помилка</Badge> : x.last_sync_at ? <Badge kind="ok">працює</Badge> : null}
                <span className="muted">{x.last_sync_at ? `оновлено ${dt(x.last_sync_at, true)} · імпортовано ${x.imported}` : "ще не синхронізувався"}</span>
              </button>
              {isOpen && (
                <div className="form np-acc-b">
                  <div className="cols">
                    <Field label="Назва магазину" hint="Пишеться в додаткове поле замовлення, напр. «Rozetka(Antony_store)»"><input value={x.name} onChange={(e) => upd(x.key, { name: e.target.value })} /></Field>
                    {x.kind === "rozetka"
                      ? <Field label="Логін кабінету продавця" hint="Доступ має бути адміністраторським"><input value={x.login} autoComplete="off" onChange={(e) => upd(x.key, { login: e.target.value })} /></Field>
                      : <Field label="API-токен Prom" hint="Кабінет Prom → Налаштування → Керування API-токенами"><input className="mono" autoComplete="off" placeholder="не вказано" value={x.secret} onChange={(e) => upd(x.key, { secret: e.target.value })} /></Field>}
                  </div>
                  {x.kind === "rozetka" && <div className="cols"><Field label="Пароль кабінету продавця"><input type="password" autoComplete="new-password" placeholder={x.secret ? "збережено" : "не вказано"} value={x.secret === "********" ? "" : x.secret} onChange={(e) => upd(x.key, { secret: e.target.value || (x.id ? "********" : "") })} /></Field>
                    <Field label="Імпортувати з дати" hint="Порожньо — останні 14 днів"><input type="date" value={x.since ? x.since.slice(0, 10) : ""} onChange={(e) => upd(x.key, { since: e.target.value || null })} /></Field></div>}
                  <div className="cols c3">
                    <Field label="Відділ" hint="У який відділ іти замовленням"><select value={x.office_id ?? ""} onChange={(e) => upd(x.key, { office_id: e.target.value ? Number(e.target.value) : null })}>
                      <option value="">не вказано</option>{s.offices.filter((o) => o.active).map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</select></Field>
                    <Field label="Статус нових замовлень"><select value={x.import_status_id ?? ""} onChange={(e) => upd(x.key, { import_status_id: e.target.value ? Number(e.target.value) : null })}>
                      <option value="">як усі нові</option>{statuses.map((st) => <option key={st.id} value={st.id}>{st.name}</option>)}</select></Field>
                    <Field label="Назву магазину в поле"><select value={x.extra_field} onChange={(e) => upd(x.key, { extra_field: Number(e.target.value) })}>
                      <option value={0}>не писати</option>{[1, 2, 3, 4].map((i) => <option key={i} value={i}>{meta.extra_fields[i - 1] || `Поле ${i}`}</option>)}</select></Field>
                  </div>
                  <div className="np-sync">
                    <button type="button" className="btn sm" disabled={!x.id} onClick={() => run(x.id, "check")} title={x.id ? "" : "Спершу збережіть"}><RefreshCw size={14} /> Перевірити підключення</button>
                    <button type="button" className="btn sm" disabled={!x.id} onClick={() => run(x.id, "sync")}>Синхронізувати зараз</button>
                    {!x.id && <span className="hint">Збережіть магазин, потім перевірте підключення</span>}
                  </div>
                  {x.last_error && <p className="flash error">{x.last_error}</p>}
                  {res?.check && <div className="mp-check">
                    <b>Підключення працює.</b> Статусів маркетплейсу: {Object.keys(res.check.statuses).length}; замовлень за 30 днів: {res.check.orders_30d}.
                    {res.check.sample_parsed && <div className="hint">Останнє замовлення: №{String(res.check.sample_parsed.external_id)} · {String(res.check.sample_parsed.last_name)} {String(res.check.sample_parsed.first_name)} · {String(res.check.sample_parsed.phone)} · {String(res.check.sample_parsed.delivery_service)} · ТТН {String(res.check.sample_parsed.ttn || "—")} · оплата: {String(res.check.sample_parsed.payment || "—")} · товарів {(res.check.sample_parsed.items as unknown[]).length}</div>}
                  </div>}
                  {res?.sync && <p className="hint">Остання синхронізація: нових {res.sync.new}, оновлено {res.sync.updated}{res.sync.error ? ` · помилка: ${res.sync.error}` : ""}</p>}

                  <div className="mp-maps">
                    <div><span className="lbl">Статус у CRM → статус на {x.kind === "rozetka" ? "Rozetka" : "Prom"}</span>
                      {Object.keys(mpStatuses).length === 0 ? <p className="hint">Натисніть «Перевірити підключення», щоб завантажити статуси Rozetka.</p> :
                        <div className="mp-map">{statuses.map((st) => (
                          <div className="mp-map-row" key={st.id}><span>{st.name}</span>
                            <select value={x.status_map[String(st.id)] ?? ""} onChange={(e) => { const m = { ...x.status_map }; if (e.target.value) m[String(st.id)] = e.target.value; else delete m[String(st.id)]; upd(x.key, { status_map: m }); }}>
                              <option value="">не передавати</option>{Object.entries(mpStatuses).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></div>
                        ))}</div>}
                    </div>
                    <div><span className="lbl">Оплата на маркетплейсі → вид оплати</span>
                      {(dir.payments ?? []).length === 0 ? <p className="hint">З'являться після першої синхронізації. Поки типово: оплачено — {x.kind === "rozetka" ? "RozetkaPay" : "Пром-оплата"}, інакше — {x.kind === "rozetka" ? "Післяплата Rozetka" : "Післяплата NovaPay"}.</p> :
                        <div className="mp-map">{(dir.payments ?? []).map((n) => (
                          <div className="mp-map-row" key={n}><span>{n}</span>
                            <select value={x.payment_map[n] ?? ""} onChange={(e) => { const m = { ...x.payment_map }; if (e.target.value) m[n] = Number(e.target.value); else delete m[n]; upd(x.key, { payment_map: m }); }}>
                              <option value="">типово</option>{meta.payment_methods.map((pm) => <option key={pm.id} value={pm.id}>{pm.name}</option>)}</select></div>
                        ))}</div>}
                      {(dir.deliveries ?? []).length > 0 && <><span className="lbl" style={{ marginTop: 10, display: "block" }}>Доставка на маркетплейсі → служба доставки</span>
                        <div className="mp-map">{(dir.deliveries ?? []).map((n) => (
                          <div className="mp-map-row" key={n}><span>{n}</span>
                            <select value={x.delivery_map[n] ?? ""} onChange={(e) => { const m = { ...x.delivery_map }; if (e.target.value) m[n] = e.target.value; else delete m[n]; upd(x.key, { delivery_map: m }); }}>
                              <option value="">за назвою</option>{Object.entries(meta.delivery_methods).map(([k, nm]) => <option key={k} value={k}>{nm}</option>)}</select></div>
                        ))}</div></>}
                    </div>
                  </div>
                  <div className="form-actions">
                    <label className="check"><input type="checkbox" checked={x.is_active} onChange={(e) => upd(x.key, { is_active: e.target.checked })} /> Активний</label>
                    <span className="spacer" />
                    <button type="button" className="btn sm danger" onClick={() => { if (window.confirm("Відключити магазин? Імпортовані замовлення залишаться.")) { if (x.id) upd(x.key, { delete: true }); else setRows(rows.filter((r) => r.key !== x.key)); } }}><Trash2 size={13} /> Відключити</button>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
      {rows.length > 0 && <div className="form-actions mt"><button type="button" className="btn primary" disabled={save.isPending} onClick={submit}>Зберегти</button></div>}
    </div>
  );
}

// ---------------------------------------------------------------- Checkbox
type CashRow = Cashier & { key: string; delete?: boolean };
const COND = { none: "Без умови (для всіх)", office: "Відділ замовлення", user: "Менеджер замовлення", np_account: "Відправник ТТН (ключ НП)" };

function CheckboxSettings({ s }: { s: S }) {
  const save = useSave();
  const toast = useToast();
  const [rows, setRows] = useState<CashRow[]>(() => s.cashiers.map((c) => ({ ...c, key: rk() })));
  const auto = useForm(s, ["cb_sell_status", "cb_return_status", "cb_prepay_status", "cb_postpay_status"]);
  const upd = (key: string, patch: Partial<CashRow>) => setRows(rows.map((r) => (r.key === key ? { ...r, ...patch } : r)));
  const move = (i: number, d: number) => { const a = [...rows]; const j = i + d; if (j < 0 || j >= a.length) return; [a[i], a[j]] = [a[j], a[i]]; setRows(a); };
  const visible = rows.map((r, i) => [r, i] as const).filter(([r]) => !r.delete);
  const options = (c: CashRow): [number, string][] => c.condition === "office" ? s.offices.filter((o) => o.active).map((o) => [o.id, o.name])
    : c.condition === "user" ? s.users.filter((u) => u.is_active).map((u) => [u.id, u.name])
    : c.condition === "np_account" ? s.np_accounts.map((a) => [a.id, a.name || `Ключ ${a.id}`]) : [];
  const check = async (id: number) => { try { const r = await api.post<{ message: string }>(`/settings/checkbox-cashiers/${id}/check`); toast(r.message); } catch (e) { toast(errText(e), "error"); } };
  const statuses = s.statuses.filter((x) => x.active);
  const byEntity = s.legal_entities.length > 0;
  return (
    <div className="stack">
      <div className="card">
        <div className="card-head"><h2>Каси Checkbox <span className="muted">{visible.length}</span></h2>
          <button type="button" className="btn sm" onClick={() => setRows([...rows, { id: 0, name: "", license_key: "", login: "", password: "", test_mode: false, auto_shift: true, legal_entity_id: null, condition: "none", condition_value: null, sort: 0, is_active: true, last_error: "", key: rk() }])}><Plus size={14} /> Додати касу</button></div>
        <p className="hint">{byEntity ? "Каса обирається за юрособою замовлення (вкладка «Юрособи»). Одна юрособа — одна каса." : "Одна каса — один ФОП. Для чека береться перша каса згори, умова якої підходить до замовлення. Порада: заведіть юрособи — тоді каса обиратиметься за юрособою замовлення."} Тип оплати в чеку — з виду оплати (Довідники → Види оплат, колонка «Checkbox»).</p>
        {visible.length === 0 && <Empty>Кас ще немає. Ключ ліцензії, логін і пароль касира — у кабінеті Checkbox.</Empty>}
        <div className="np-accs">
          {visible.map(([c, i]) => (
            <div className="np-acc open" key={c.key}>
              <div className="form np-acc-b cb-row">
                <div className="cols">
                  <Field label="ПІБ касира" hint="Друкується в чеку"><input value={c.name} onChange={(e) => upd(c.key, { name: e.target.value })} /></Field>
                  <Field label="Ключ ліцензії каси" hint="Кабінет Checkbox → Каси"><input className="mono" autoComplete="off" placeholder="не вказано" value={c.license_key} onChange={(e) => upd(c.key, { license_key: e.target.value })} /></Field>
                </div>
                <div className="cols">
                  <Field label="Логін касира"><input value={c.login} autoComplete="off" onChange={(e) => upd(c.key, { login: e.target.value })} /></Field>
                  <Field label="Пароль касира"><input type="password" autoComplete="new-password" placeholder={c.password ? "збережено" : "не вказано"} value={c.password === "********" ? "" : c.password} onChange={(e) => upd(c.key, { password: e.target.value || (c.id ? "********" : "") })} /></Field>
                </div>
                {byEntity ? (
                  <Field label="Юрособа" hint="Чеки замовлень цієї юрособи йдуть через цю касу"><select value={c.legal_entity_id ?? ""} required onChange={(e) => upd(c.key, { legal_entity_id: e.target.value ? Number(e.target.value) : null })}>
                    <option value="">оберіть юрособу</option>{s.legal_entities.map((x) => <option key={x.id} value={x.id}>{x.name}{x.is_default ? " (за замовч.)" : ""}</option>)}</select></Field>
                ) : (
                <div className="cols">
                  <Field label="Умова вибору каси"><select value={c.condition} onChange={(e) => upd(c.key, { condition: e.target.value as Cashier["condition"], condition_value: null })}>
                    {Object.entries(COND).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></Field>
                  {c.condition !== "none" && <Field label="Значення"><select value={c.condition_value ?? ""} onChange={(e) => upd(c.key, { condition_value: e.target.value ? Number(e.target.value) : null })}>
                    <option value="">оберіть</option>{options(c).map(([id, n]) => <option key={id} value={id}>{n}</option>)}</select></Field>}
                </div>
                )}
                {c.last_error && <p className="flash error">{c.last_error}</p>}
                <div className="form-actions">
                  <label className="check" title="Відкривати зміну перед першим чеком і закривати о 23:00"><input type="checkbox" checked={c.auto_shift} onChange={(e) => upd(c.key, { auto_shift: e.target.checked })} /> Автозміни</label>
                  <label className="check" title="Тестовий сервер Checkbox — чеки не фіскальні"><input type="checkbox" checked={c.test_mode} onChange={(e) => upd(c.key, { test_mode: e.target.checked })} /> Тестова каса</label>
                  <label className="check"><input type="checkbox" checked={c.is_active} onChange={(e) => upd(c.key, { is_active: e.target.checked })} /> Активна</label>
                  <span className="spacer" />
                  <button type="button" className="x" title="Вище" onClick={() => move(i, -1)}><ArrowUp size={13} /></button>
                  <button type="button" className="x" title="Нижче" onClick={() => move(i, 1)}><ArrowDown size={13} /></button>
                  <button type="button" className="btn sm" disabled={!c.id} onClick={() => check(c.id)}>Перевірити</button>
                  <button type="button" className="btn sm danger" onClick={() => (c.id ? upd(c.key, { delete: true }) : setRows(rows.filter((r) => r.key !== c.key)))}><Trash2 size={13} /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
        {rows.length > 0 && <div className="form-actions mt"><button type="button" className="btn primary" disabled={save.isPending}
          onClick={() => save.mutate({ path: "/settings/checkbox-cashiers", method: "put", body: rows.map(({ key: _k, last_error: _e, sort: _s, ...r }) => ({ ...r, id: r.id || undefined })) }, { onSuccess: (x) => setRows((x as S).cashiers.map((c) => ({ ...c, key: rk() }))) })}>Зберегти каси</button></div>}
      </div>
      <form className="card form" onSubmit={(e) => { e.preventDefault(); save.mutate({ path: "/settings/checkbox", body: auto.v }); }}>
        <h2>Автоматичні чеки</h2>
        <p className="hint">Чек створюється сам, коли замовлення переходить у вибраний статус (один раз на замовлення).</p>
        <div className="cols">
          {([["cb_sell_status", "Чек продажу"], ["cb_return_status", "Чек повернення"], ["cb_prepay_status", "Чек передоплати"], ["cb_postpay_status", "Чек післяплати"]] as const).map(([k, n]) => (
            <Field key={k} label={n}><select {...auto.bind(k)}><option value="">вручну</option>{statuses.map((x) => <option key={x.id} value={x.id}>{x.name}</option>)}</select></Field>
          ))}
        </div>
        <div className="form-actions"><button className="btn primary" disabled={save.isPending}>Зберегти</button></div>
      </form>
    </div>
  );
}


// ---------------------------------------------------------------- юридичні особи
type EntRow = LegalEntity & { key: string; delete?: boolean };

function LegalEntities({ s }: { s: S }) {
  const save = useSave();
  const [rows, setRows] = useState<EntRow[]>(() => s.legal_entities.map((x) => ({ ...x, key: rk() })));
  const upd = (key: string, patch: Partial<EntRow>) => setRows(rows.map((r) => (r.key === key ? { ...r, ...patch } : r)));
  const visible = rows.filter((r) => !r.delete);
  const submit = () => save.mutate({ path: "/settings/legal-entities", body: rows.filter((r) => r.name.trim() || r.delete).map((r) => ({
    id: r.id || undefined, name: r.name, code: r.code, iban: r.iban, is_default: r.is_default, is_active: r.is_active, delete: !!r.delete })) },
    { onSuccess: (x) => setRows((x as S).legal_entities.map((y) => ({ ...y, key: rk() }))) });
  return (
    <div className="card">
      <div className="card-head"><h2><Building2 size={16} /> Юридичні особи <span className="muted">{visible.length}</span></h2>
        <button type="button" className="btn sm" onClick={() => setRows([...rows, { id: 0, name: "", code: "", iban: "", is_default: rows.length === 0, is_active: true, sort: 0, orders: 0, cashier: "", key: rk() }])}><Plus size={14} /> Додати</button></div>
      <p className="hint">ФОП або ТОВ, від імені якого продається замовлення. У кожному замовленні юрособу можна змінити; нові замовлення отримують юрособу за замовчуванням.
        За юрособою обирається каса Checkbox (вкладка «Checkbox») і ключ Нової Пошти (вкладка «Доставка»).</p>
      {visible.length === 0 && <Empty><Building2 size={22} className="e-ico" />Юросіб ще немає. Додайте, наприклад, «ФОП Максимчук О. В.».</Empty>}
      <div className="ent-list">
        {visible.map((r) => (
          <div key={r.key} className={`ent-row ${r.is_active ? "" : "off"}`}>
            <button type="button" className={`ent-star ${r.is_default ? "on" : ""}`} title={r.is_default ? "За замовчуванням" : "Зробити юрособою за замовчуванням"}
              onClick={() => setRows(rows.map((x) => ({ ...x, is_default: x.key === r.key })))}><Star size={16} /></button>
            <input value={r.name} onChange={(e) => upd(r.key, { name: e.target.value })} placeholder="ФОП Прізвище І. П." />
            <input className="mono" value={r.code} onChange={(e) => upd(r.key, { code: e.target.value })} placeholder="ЄДРПОУ / РНОКПП" />
            <input className="mono" value={r.iban} onChange={(e) => upd(r.key, { iban: e.target.value })} placeholder="IBAN (необов'язково)" />
            <span className="ent-meta">{r.cashier ? <Badge kind="ok">каса: {r.cashier}</Badge> : r.id ? <Badge kind="warn">без каси</Badge> : null}{r.orders > 0 && <span className="muted"> {r.orders} замовл.</span>}</span>
            <label className="mini-check"><input type="checkbox" checked={r.is_active} onChange={(e) => upd(r.key, { is_active: e.target.checked })} /> активна</label>
            <button type="button" className="x" title="Прибрати" onClick={() => (r.id ? upd(r.key, { delete: true }) : setRows(rows.filter((x) => x.key !== r.key)))}>×</button>
          </div>
        ))}
      </div>
      <div className="form-actions mt"><span className="spacer" /><button type="button" className="btn primary" disabled={save.isPending} onClick={submit}>Зберегти юрособи</button></div>
    </div>
  );
}

// ---------------------------------------------------------------- покупці: групи й заблоковані IP
function CustomerSettings() {
  const qc = useQueryClient();
  const toast = useToast();
  const groups = useQuery({ queryKey: ["customer-groups"], queryFn: () => api.get<CustomerGroup[]>("/customer-groups") });
  const ips = useQuery({ queryKey: ["blocked-ips"], queryFn: () => api.get<BlockedIp[]>("/blocked-ips") });
  const [ng, setNg] = useState({ name: "", color: "#64748b" });
  const [nip, setNip] = useState({ ip: "", comment: "" });
  const mut = useMutation({
    mutationFn: ({ method, url, body }: { method: "post" | "del"; url: string; body?: Record<string, unknown> }) => method === "del" ? api.del<unknown>(url) : api.post<unknown>(url, body),
    onSuccess: (data, v) => { qc.setQueryData([v.url.includes("blocked") ? "blocked-ips" : "customer-groups"], data); qc.invalidateQueries({ queryKey: ["meta"] }); toast("Збережено"); },
    onError: (e) => toast(errText(e), "error"),
  });
  return (
    <div className="grid half">
      <div className="card">
        <h2>Групи покупців</h2>
        <p className="hint">Покупець, оптовик, дропшипер, партнер… Групу видно в картці замовлення й у розділі «Покупці».</p>
        <div className="dir-list">
          {groups.data?.map((g) => (
            <div key={g.id} className="dir-row">
              <input type="color" value={g.color} onChange={(e) => mut.mutate({ method: "post", url: "/customer-groups", body: { id: g.id, name: g.name, color: e.target.value } })} />
              <input defaultValue={g.name} onBlur={(e) => e.target.value.trim() && e.target.value !== g.name && mut.mutate({ method: "post", url: "/customer-groups", body: { id: g.id, name: e.target.value, color: g.color } })} />
              <span className="muted nowrap">{g.customers} покупц.</span>
              <button type="button" className="x" title="Видалити групу" onClick={() => window.confirm(`Видалити групу «${g.name}»? Покупці залишаться без групи.`) && mut.mutate({ method: "del", url: `/customer-groups/${g.id}` })}>×</button>
            </div>
          ))}
        </div>
        <form className="dir-add-row" onSubmit={(e) => { e.preventDefault(); mut.mutate({ method: "post", url: "/customer-groups", body: ng }); setNg({ ...ng, name: "" }); }}>
          <input type="color" value={ng.color} onChange={(e) => setNg({ ...ng, color: e.target.value })} />
          <input value={ng.name} onChange={(e) => setNg({ ...ng, name: e.target.value })} placeholder="Нова група" required />
          <button className="btn"><Plus size={14} /> Додати</button>
        </form>
      </div>
      <div className="card">
        <h2>Заблоковані IP-адреси</h2>
        <p className="hint">Заявки з лендингів із цих адрес не приймаються (захист від спаму й ботів). IP видно в картці замовлення, блок «Сайт і UTM-мітки».</p>
        <div className="dir-list">
          {ips.data?.map((x) => (
            <div key={x.id} className="dir-row"><span className="mono">{x.ip}</span><span className="muted">{x.comment}</span><span className="spacer" />
              <button type="button" className="x" title="Розблокувати" onClick={() => mut.mutate({ method: "del", url: `/blocked-ips/${x.id}` })}>×</button></div>
          ))}
          {ips.data && !ips.data.length && <p className="hint">Немає заблокованих адрес.</p>}
        </div>
        <form className="dir-add-row" onSubmit={(e) => { e.preventDefault(); mut.mutate({ method: "post", url: "/blocked-ips", body: nip }); setNip({ ip: "", comment: "" }); }}>
          <input className="mono" value={nip.ip} onChange={(e) => setNip({ ...nip, ip: e.target.value })} placeholder="IP-адреса" required />
          <input value={nip.comment} onChange={(e) => setNip({ ...nip, comment: e.target.value })} placeholder="Причина" />
          <button className="btn"><Plus size={14} /> Заблокувати</button>
        </form>
      </div>
    </div>
  );
}
