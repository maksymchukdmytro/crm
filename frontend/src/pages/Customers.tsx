// Покупці: один запис на телефон; замовлення, викуп і відмови рахуються із замовлень. Групи й чорний список.
import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Ban, Check, ChevronLeft, Contact, LockOpen, MessageCircle, MessageSquare, MoreHorizontal, Phone, Plus, Send, X } from "lucide-react";
import { api, qs } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { date, money, phone } from "../lib/format";
import type { CustomerDetail, CustomerList } from "../lib/types";
import { Block, Button, Empty, Field, IconButton, MenuButton, MobileActs, Modal, RoundButton, Spinner, StatusPill, Tag, Toggle, UaPhone, Window, useMobile , Select, EmptyState } from "../components/ui";
import OrderModal from "./OrderCard";
import "./customers.css";

const SORTS: [string, string][] = [["last", "Останнє замовлення"], ["orders", "Кількість замовлень"], ["sum", "Сума отриманих"],
  ["refused", "Відмови"], ["buyout", "Викуп"], ["created", "Дата додавання"], ["name", "Ім'я"]];

export default function CustomersPage() {
  const meta = useMeta();
  const nav = useNavigate();
  const { id } = useParams();
  const [q, setQ] = useState("");
  const [group, setGroup] = useState("");
  const [blacklist, setBlacklist] = useState("");
  const [sort, setSort] = useState("last");
  const [desc, setDesc] = useState(true);
  const [page, setPage] = useState(0);
  const [sp, setSp] = useSearchParams();
  const [adding, setAdding] = useState(() => !!sp.get("new"));
  useEffect(() => { if (sp.get("new")) { setAdding(true); const n = new URLSearchParams(sp); n.delete("new"); setSp(n, { replace: true }); } }, [sp, setSp]);
  const dq = useDebounced(q, 300);
  useEffect(() => setPage(0), [dq, group, blacklist, sort, desc]);
  const params = { q: dq, group, blacklist, sort, desc, offset: page * 100, limit: 100 };
  const mobile = useMobile();
  const { data, isFetching } = useQuery({ queryKey: ["customers", params], queryFn: () => api.get<CustomerList>(`/customers${qs(params)}`), placeholderData: keepPreviousData });

  return (
    <div className="customers">
      <div className="head">
        <h1><span className="h-ico"><Contact size={18} /></span>Покупці <small className="muted">{data?.total ?? ""}</small> {isFetching && <span className="spinner sm" />}</h1>
        <div className="actions"><button className="btn primary" onClick={() => setAdding(true)}><Plus size={15} /> Покупець</button></div>
      </div>
      <div className="cu-groups">
        <button className={!group && !blacklist ? "on" : ""} onClick={() => { setGroup(""); setBlacklist(""); }}>Усі</button>
        {meta.customer_groups.map((g) => (
          <button key={g.id} className={group === String(g.id) ? "on" : ""} style={{ ["--c" as string]: g.color }} onClick={() => { setGroup(String(g.id)); setBlacklist(""); }}>
            <i />{g.name}</button>
        ))}
        <button className={`bl ${blacklist === "1" ? "on" : ""}`} onClick={() => { setBlacklist(blacklist === "1" ? "" : "1"); setGroup(""); }}><Ban size={13} /> Чорний список</button>
      </div>
      <div className="filters">
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ім'я, телефон або email" />
        <span className="cu-sort">
          <Select value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Сортування">{SORTS.map(([k, v]) => <option key={k} value={k}>{v}</option>)}</Select>
          <button className="btn icon" title={desc ? "За спаданням" : "За зростанням"} onClick={() => setDesc((d) => !d)}>{desc ? <ArrowDown size={15} /> : <ArrowUp size={15} />}</button>
        </span>
      </div>
      <MobileActs><RoundButton icon={Plus} label="Новий покупець" primary onClick={() => setAdding(true)} /></MobileActs>
      {mobile && <p className="list-sum cu-msum">{data ? `${money(data.total)} ${data.total % 10 === 1 && data.total % 100 !== 11 ? "покупець" : "покупців"}` : ""}</p>}
      {mobile && (
        <div className="m-list">
          {!data && Array.from({ length: 4 }, (_, i) => <div key={i} className="m-card m-skel" aria-hidden><i /><i /><i /></div>)}
          {data?.rows.map((c) => {
            const ini = (c.name || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
            const col = c.blacklisted ? "#DC2626" : c.group_color || "#3557A8";
            return (
              <div key={c.id} role="button" tabIndex={0} className="m-card cu-mcard" onClick={() => nav(`/customers/${c.id}`)}
                onKeyDown={(e) => { if (e.key === "Enter") nav(`/customers/${c.id}`); }}>
                <span className="m-av" style={{ background: `color-mix(in srgb, ${col} 13%, white)`, color: col }}>{ini}</span>
                <div className="cu-mt">
                  <div className="cu-m1"><b className="ell">{c.name || "Без імені"}</b><b className="num">{money(c.sum_delivered)} ₴</b></div>
                  <small>{phone(c.phone)}</small>
                  <div className="cu-m3">
                    {c.blacklisted ? <span className="pill" style={{ ["--c" as string]: "#DC2626" }}>чорний список</span>
                      : c.group ? <span className="pill" style={{ ["--c" as string]: c.group_color || "#64748b" }}>{c.group}</span> : null}
                    <span>{c.orders} замовл. · викуп <b className={c.buyout_rate == null ? "" : c.buyout_rate >= 70 ? "t-ok" : c.buyout_rate >= 40 ? "t-warn" : "t-bad"}>{c.buyout_rate == null ? "—" : `${c.buyout_rate}%`}</b></span>
                  </div>
                </div>
              </div>
            );
          })}
          {data && !data.rows.length && <div className="m-card m-empty">{dq ? <Empty>Нікого не знайдено</Empty> : <EmptyState icon={Contact} title="Покупців ще немає" text="Покупець з'являється сам із першим замовленням на його телефон" action={{ label: "Нове замовлення", icon: Plus, onClick: () => nav("/orders/new") }} />}</div>}
        </div>
      )}
      {!mobile && <div className="card flush tablewrap">
        <table className="t cu-table m-cards">
          <thead><tr><th>Покупець</th><th>Група</th><th className="num">Замовлень</th><th className="num">Отримано</th><th className="num">Відмов</th>
            <th className="num">Викуп</th><th className="num">Сума отриманих</th><th>Останнє</th></tr></thead>
          <tbody>
            {!data && <tr><td colSpan={8}><Empty><Spinner /></Empty></td></tr>}
            {data?.rows.map((c) => (
              <tr key={c.id} className={`clickable ${c.blacklisted ? "is-bl" : ""}`} onClick={() => nav(`/customers/${c.id}`)}>
                <td><div className="cu-name">{c.blacklisted && <Ban size={14} className="bl-ico" />}{c.name || <span className="muted">Без імені</span>}</div>
                  <span className="sub">{phone(c.phone)}{c.email && ` · ${c.email}`}</span></td>
                <td>{c.group ? <span className="pill" style={{ ["--c" as string]: c.group_color || "#64748b" }}>{c.group}</span> : <span className="muted">—</span>}</td>
                <td className="num"><b>{c.orders}</b></td><td className="num">{c.delivered || ""}</td>
                <td className={`num ${c.refused ? "lowstock" : ""}`}>{c.refused || ""}</td>
                <td className="num">{c.buyout_rate == null ? <span className="muted">—</span> : <span className={`rate ${c.buyout_rate >= 70 ? "hi" : c.buyout_rate >= 40 ? "mid" : "lo"}`}>{c.buyout_rate}%</span>}</td>
                <td className="num">{c.sum_delivered ? `${money(c.sum_delivered)} ₴` : ""}</td>
                <td className="muted nowrap">{date(c.last_order_at)}</td>
              </tr>
            ))}
            {data && !data.rows.length && <tr><td colSpan={8}><Empty>{dq ? "Нікого не знайдено" : "Покупці з'являться із першими замовленнями"}</Empty></td></tr>}
          </tbody>
        </table>
      </div>}
      {data && data.total > 100 && (
        <div className="cu-pages">
          <button className="btn sm" disabled={!page} onClick={() => setPage((p) => p - 1)}>Назад</button>
          <span className="muted">{page * 100 + 1}–{Math.min(data.total, (page + 1) * 100)} з {data.total}</span>
          <button className="btn sm" disabled={(page + 1) * 100 >= data.total} onClick={() => setPage((p) => p + 1)}>Далі</button>
        </div>
      )}
      {id && <CustomerCard id={Number(id)} onClose={() => nav("/customers")} />}
      {adding && <NewCustomer onClose={() => setAdding(false)} onCreated={(cid) => { setAdding(false); nav(`/customers/${cid}`); }} />}
    </div>
  );
}

function CustomerCard({ id, onClose }: { id: number; onClose: () => void }) {
  const meta = useMeta();
  const nav = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();
  const { data } = useQuery({ queryKey: ["customer", id], queryFn: () => api.get<CustomerDetail>(`/customers/${id}`) });
  const [f, setF] = useState<Record<string, string | boolean | number | null>>({});
  const [order, setOrder] = useState<number | null>(null);
  useEffect(() => setF({}), [id]);
  const v = <T,>(k: string, d: T): T => (k in f ? (f[k] as T) : data ? ((data as unknown as Record<string, T>)[k] ?? d) : d);
  const save = useMutation({
    mutationFn: (patch: Record<string, unknown>) => api.patch<CustomerDetail>(`/customers/${id}`, patch),
    onSuccess: (c) => { qc.setQueryData(["customer", id], c); qc.invalidateQueries({ queryKey: ["customers"] }); setF({}); toast("Збережено"); },
    onError: (e) => toast(errText(e), "error"),
  });
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") { e.preventDefault(); if (Object.keys(f).length) save.mutate(f); } };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  });
  const mobile = useMobile();
  const statuses = Object.fromEntries(meta.statuses.map((s) => [s.id, s]));
  const pm = Object.fromEntries(meta.payment_methods.map((m) => [m.id, m]));
  if (!data) return <Window size="sm" onClose={onClose} title="Покупець"><Empty><Spinner /></Empty></Window>;
  const comms = data.communications ?? [], addrs = data.addresses ?? [], marks = data.marks ?? [], sources = data.sources ?? [];
  const bl = v("blacklisted", false);
  const dirty = Object.keys(f).length > 0;
  const tel = data.phone.replace(/\D/g, "");
  const initials = (data.name || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
  const since = data.first_order_at ? new Date(data.first_order_at).toLocaleDateString("uk-UA", { month: "long", year: "numeric" }) : "";
  const head = (
    <div className="win-head cw-head">
      <IconButton icon={ChevronLeft} label="Назад (Esc)" quiet onClick={onClose} />
      <h2>Покупець</h2>
      {data.group && <span className="badge" style={{ background: `color-mix(in srgb, ${data.group_color || "#64748b"} 14%, white)`, color: data.group_color || undefined }}>{data.group}</span>}
      {data.blacklisted && <Tag kind="bad" icon={<Ban size={11} />}>Чорний список</Tag>}
      <div className="acts">
        <Button variant="soft" icon={Plus} onClick={() => nav(`/orders/new?phone=${data.phone}`)}>Нове замовлення</Button>
        <Button variant="danger" icon={Ban} onClick={() => setF({ ...f, blacklisted: !bl })}>{bl ? "Зняти з чорного списку" : "У чорний список"}</Button>
        <Button variant="primary" icon={Check} disabled={!dirty || save.isPending} onClick={() => save.mutate(f)}>Зберегти</Button>
        <IconButton icon={X} label="Закрити (Esc)" quiet onClick={onClose} />
      </div>
    </div>
  );
  // телефон (мобільна v2): «‹ Покупець ⋯», картка з аватаром і кнопками зв'язку, плитки, далі блоки; знизу «Нове замовлення» або «Зберегти»
  const mhead = (
    <div className="oc-mhead">
      <RoundButton icon={ChevronLeft} label="Назад" onClick={onClose} />
      <div className="oc-mhead-t"><b>Покупець</b>{since && <small>з {since}</small>}</div>
      <MenuButton button={({ open, toggle }) => <button type="button" className="rb" aria-label="Ще дії" aria-expanded={open} onClick={toggle}><MoreHorizontal size={20} /></button>}>
        {(close) => (
          <button className="pop-item" onClick={() => { close(); setF({ ...f, blacklisted: !bl }); }}><Ban size={16} />{bl ? "Зняти з чорного списку" : "У чорний список"}</button>
        )}
      </MenuButton>
    </div>
  );
  const mhero = mobile && (
    <section className="cw-mhero">
      <div className="cw-mhero-1">
        <span className="m-av lg" style={data.group_color ? { background: `color-mix(in srgb, ${data.group_color} 13%, white)`, color: data.group_color } : undefined}>{initials}</span>
        <div className="cw-mhero-t"><b className="ell">{data.name || "Без імені"}</b><span>{phone(data.phone)}</span></div>
        {data.group && <span className="pill" style={{ ["--c" as string]: data.group_color || "#64748b" }}>{data.group}</span>}
        {bl && <span className="pill" style={{ ["--c" as string]: "#DC2626" }}>ЧС</span>}
      </div>
      <div className="oc-hero-msg">
        <a className="p" href={`tel:+${tel}`} aria-label="Подзвонити"><Phone size={18} /></a>
        <a href={`viber://chat?number=%2B${tel}`} aria-label="Viber"><MessageCircle size={18} /></a>
        <a href={`https://t.me/+${tel}`} target="_blank" rel="noreferrer" aria-label="Telegram"><Send size={18} /></a>
        <a href={`sms:+${tel}`} aria-label="SMS"><MessageSquare size={18} /></a>
      </div>
      <div className="cw-mtiles">
        <div><b>{data.orders}</b><small>замовлень</small></div>
        <div><b className={data.buyout_rate != null && data.buyout_rate < 50 ? "t-bad" : ""}>{data.buyout_rate == null ? "—" : `${Math.round(data.buyout_rate)}%`}</b><small>викуп</small></div>
        <div><b>{data.refused}</b><small>відмов</small></div>
        <div><b>{data.sum_delivered >= 10000 ? `${(data.sum_delivered / 1000).toLocaleString("uk-UA", { maximumFractionDigits: 1 })}к` : money(data.sum_delivered)}</b><small>сума, ₴</small></div>
      </div>
    </section>
  );
  const mbar = mobile && (
    <div className="oc-mbar">
      <button type="button" className={`rb${bl ? " bad" : ""}`} aria-label={bl ? "Зняти з чорного списку" : "У чорний список"} onClick={() => setF({ ...f, blacklisted: !bl })}>
        {bl ? <LockOpen size={20} /> : <Ban size={20} />}</button>
      {dirty
        ? <Button variant="primary" icon={Check} disabled={save.isPending} onClick={() => save.mutate(f)}>Зберегти</Button>
        : <Button variant="primary" icon={Plus} onClick={() => nav(`/orders/new?phone=${data.phone}`)}>Нове замовлення</Button>}
    </div>
  );
  return (
    <Window size="xl" onClose={onClose} head={mobile ? mhead : head} label={data.name || "Покупець"} bodyClass="cw-body">
      {mhero}
      {mbar}
      <div className="cw-grid">
        <div className="cw-col">
          <Block title="Профіль" className="cw-profile">
            <div className="cw-hero">
              <span className="cw-av">{initials}</span>
              <div><div className="cw-name">{data.name || "Без імені"}</div>
                <small className="muted">{since ? `покупець з ${since}` : "ще без замовлень"}{sources[0] ? ` · перше замовлення з ${sources[0]}` : ""}</small></div>
            </div>
            <div className="oc-phone-row">
              <span className="phone-pill-in"><Phone size={14} className="muted" />
                <UaPhone value={"phone" in f ? String(f.phone) : data.phone} country={data.country || "UA"} onChange={(x) => setF({ ...f, phone: x })} aria-label="Телефон" /></span>
              <a className="icon-btn" href={`tel:+${tel}`} aria-label="Подзвонити" title="Подзвонити"><Phone size={16} /></a>
              <a className="icon-btn" href={`viber://chat?number=%2B${tel}`} aria-label="Viber" title="Viber"><MessageCircle size={16} /></a>
              <a className="icon-btn" href={`https://t.me/+${tel}`} target="_blank" rel="noreferrer" aria-label="Telegram" title="Telegram"><Send size={16} /></a>
              <a className="icon-btn" href={`sms:+${tel}`} aria-label="SMS" title="SMS"><MessageSquare size={16} /></a>
            </div>
            <div className="pw-2">
              <Field label="Ім'я"><input value={v("name", "")} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
              <Field label="Email"><input type="email" value={v("email", "")} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
              <Field label="Група"><Select value={v<number | null>("group_id", null) ?? ""} onChange={(e) => setF({ ...f, group_id: e.target.value ? Number(e.target.value) : null })}>
                <option value="">без групи</option>{meta.customer_groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}</Select></Field>
              <Field label="Додатковий телефон"><UaPhone value={"phone2" in f ? String(f.phone2) : String(v("phone2", "") || "")} onChange={(x) => setF({ ...f, phone2: x })} aria-label="Додатковий телефон" /></Field>
            </div>
            <Field label="Коментар"><textarea rows={2} value={v("comment", "")} onChange={(e) => setF({ ...f, comment: e.target.value })} placeholder="Бачать менеджери в картці замовлення" /></Field>
            <div className="tiles4">
              <div><b>{data.orders}</b><span>Замовлень</span></div>
              <div className={data.buyout_rate != null && data.buyout_rate < 50 ? "warn" : ""}><b>{data.buyout_rate == null ? "—" : `${Math.round(data.buyout_rate)}%`}</b><span>Викуп</span></div>
              <div><b>{data.refused}</b><span>Відмов</span></div>
              <div><b>{money(data.sum_delivered)}</b><span>Сума, ₴</span></div>
            </div>
          </Block>
          <Block title="Чорний список" className="cw-bl">
            <Toggle checked={bl} onChange={(c) => setF({ ...f, blacklisted: c })} label={bl ? "У чорному списку" : "Не в чорному списку"} />
            {bl && <input className="cw-reason" value={v("blacklist_reason", "")} onChange={(e) => setF({ ...f, blacklist_reason: e.target.value })} placeholder="Причина, напр. «не забирає посилки»" aria-label="Причина" />}
            <p className="hint cw-hint">Нові замовлення з цього номера отримають позначку й попередження.</p>
          </Block>
        </div>
        <div className="cw-col cw-right">
          <Block title="Замовлення" sub={mobile ? String(data.history.length) : `${data.history.length} · клік відкриває замовлення в цьому ж вікні`} className="cw-ords">
            {data.history.length ? (
              <div className="cw-orders" role="table">
                <div className="cw-orow head" role="row"><span>№</span><span>Дата</span><span>Товари</span><span>Статус</span><span>Оплата</span><span>Доставка</span><span className="a-r">Сума</span></div>
                {data.history.map((o) => (
                  <button key={o.id} type="button" className="cw-orow" role="row" onClick={() => setOrder(o.id)}>
                    <span className="mono link">{o.id}</span><span className="muted num">{date(o.created_at).slice(0, 5)}</span>
                    <span className="ell">{o.items[0]?.name}{o.items.length > 1 ? ` +${o.items.length - 1}` : ""}</span>
                    <span><StatusPill status={statuses[o.status_id]} /></span>
                    <span className="ell">{pm[o.payment_method_id ?? 0]?.name ?? "—"}</span>
                    <span className="ell">{o.city_name ? `${meta.delivery_methods[o.delivery_method] === "Нова Пошта" ? "НП" : meta.delivery_methods[o.delivery_method]} · ${o.city_name}` : "—"}</span>
                    <b className="num a-r">{money(o.total)} ₴</b>
                  </button>
                ))}
              </div>
            ) : <p className="hint">Замовлень ще немає.</p>}
          </Block>
          <div className="cw-bottom">
            <Block title="Комунікації">
              {comms.length ? (
                <ul className="cw-comms">{comms.map((c, i) => (
                  <li key={i}>{c.kind === "call" ? <Phone size={14} /> : <MessageSquare size={14} />}<span className="ell">{c.kind === "call" ? c.text : `${c.kind === "viber" ? "Viber" : "SMS"} · ${c.text}`}</span>
                    <span className="muted num">{c.at ? new Date(c.at).toLocaleString("uk-UA", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" }) : ""}</span>
                    {c.state && <span className="badge">{c.state}</span>}</li>
                ))}</ul>
              ) : <p className="hint">Повідомлень і дзвінків ще не було.</p>}
            </Block>
            <Block title="Адреси доставки">
              {addrs.length ? <ul className="cw-addr">{addrs.map((a) => <li key={a.text}><span>{a.text}</span><span className="muted">{a.count} {a.count === 1 ? "раз" : a.count < 5 ? "рази" : "разів"}</span></li>)}</ul>
                : <p className="hint">Адрес ще немає.</p>}
              {marks.length > 0 && <div className="cw-tags"><span className="muted">Позначки</span>{marks.map((m) => <span key={m.id} className="badge" style={{ color: m.color }}>{m.name}</span>)}</div>}
              {sources.length > 0 && <div className="cw-tags"><span className="muted">Джерела</span>{sources.map((x) => <span key={x} className="o-dot-txt"><i style={{ background: "var(--accent)" }} />{x}</span>)}</div>}
            </Block>
          </div>
        </div>
      </div>
      {order && <OrderModal id={String(order)} onClose={() => { setOrder(null); qc.invalidateQueries({ queryKey: ["customer", id] }); }} onOpen={(oid) => setOrder(oid)} />}
    </Window>
  );
}

function NewCustomer({ onClose, onCreated }: { onClose: () => void; onCreated: (id: number) => void }) {
  const meta = useMeta();
  const toast = useToast();
  const qc = useQueryClient();
  const [f, setF] = useState({ phone: "", name: "", email: "", group_id: "" as number | "" });
  const create = useMutation({
    mutationFn: () => api.post<CustomerDetail>("/customers", { ...f, group_id: f.group_id || null }),
    onSuccess: (c) => { qc.invalidateQueries({ queryKey: ["customers"] }); toast("Покупця додано"); onCreated(c.id); },
    onError: (e) => toast(errText(e), "error"),
  });
  return (
    <Modal onClose={onClose} size="sm" title="Новий покупець">
      <form className="form" onSubmit={(e) => { e.preventDefault(); create.mutate(); }}>
        <Field label="Телефон"><UaPhone value={f.phone} onChange={(x) => setF({ ...f, phone: x })} required autoFocus aria-label="Телефон" /></Field>
        <Field label="Ім'я"><input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
        <Field label="Email"><input type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
        <Field label="Група"><Select value={f.group_id} onChange={(e) => setF({ ...f, group_id: e.target.value ? Number(e.target.value) : "" })}>
          <option value="">за замовчуванням</option>{meta.customer_groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}</Select></Field>
        <div className="form-actions"><button className="btn primary" disabled={create.isPending}>Додати покупця</button><button type="button" className="btn" onClick={onClose}>Скасувати</button></div>
      </form>
    </Modal>
  );
}
