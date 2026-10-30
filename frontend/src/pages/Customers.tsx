// Покупці: один запис на телефон; замовлення, викуп і відмови рахуються із замовлень. Групи й чорний список.
import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowDown, ArrowUp, Ban, Contact, Plus, ShieldCheck } from "lucide-react";
import { api, qs } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { date, money, phone } from "../lib/format";
import type { CustomerDetail, CustomerList } from "../lib/types";
import { Empty, Field, Modal, Pill, Spinner } from "../components/ui";
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
          <select value={sort} onChange={(e) => setSort(e.target.value)} aria-label="Сортування">{SORTS.map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
          <button className="btn icon" title={desc ? "За спаданням" : "За зростанням"} onClick={() => setDesc((d) => !d)}>{desc ? <ArrowDown size={15} /> : <ArrowUp size={15} />}</button>
        </span>
      </div>
      <div className="card flush tablewrap">
        <table className="t cu-table">
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
      </div>
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
  useEffect(() => setF({}), [id]);
  const v = <T,>(k: string, d: T): T => (k in f ? (f[k] as T) : data ? ((data as unknown as Record<string, T>)[k] ?? d) : d);
  const save = useMutation({
    mutationFn: (patch: Record<string, unknown>) => api.patch<CustomerDetail>(`/customers/${id}`, patch),
    onSuccess: (c) => { qc.setQueryData(["customer", id], c); qc.invalidateQueries({ queryKey: ["customers"] }); setF({}); toast("Збережено"); },
    onError: (e) => toast(errText(e), "error"),
  });
  const statuses = Object.fromEntries(meta.statuses.map((s) => [s.id, s]));
  if (!data) return <Modal onClose={onClose} size="sm"><Empty><Spinner /></Empty></Modal>;
  const bl = v("blacklisted", false);
  const dirty = Object.keys(f).length > 0;
  return (
    <Modal onClose={onClose} size="lg" title={<>{data.blacklisted && <Ban size={18} className="bl-ico" />}{data.name || "Без імені"} <span className="muted cu-phone">{phone(data.phone)}</span></>}>
      <div className="cu-stats">
        <div><small>Замовлень</small><b>{data.orders}</b></div>
        <div><small>Отримано</small><b>{data.delivered}</b></div>
        <div><small>Відмов</small><b className={data.refused ? "lowstock" : ""}>{data.refused}</b></div>
        <div><small>Викуп</small><b>{data.buyout_rate == null ? "—" : `${data.buyout_rate}%`}</b></div>
        <div><small>Сума отриманих</small><b>{money(data.sum_delivered)} ₴</b></div>
        <div><small>Перше замовлення</small><b>{date(data.first_order_at) || "—"}</b></div>
      </div>
      <div className="modal-split">
        <form className="form" onSubmit={(e) => { e.preventDefault(); save.mutate(f); }}>
          <div className="cols">
            <Field label="Ім'я"><input value={v("name", "")} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
            <Field label="Телефон"><input value={"phone" in f ? String(f.phone) : phone(data.phone)} onChange={(e) => setF({ ...f, phone: e.target.value })} inputMode="tel" /></Field>
            <Field label="Email"><input type="email" value={v("email", "")} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
            <Field label="Група"><select value={v<number | null>("group_id", null) ?? ""} onChange={(e) => setF({ ...f, group_id: e.target.value ? Number(e.target.value) : null })}>
              <option value="">без групи</option>{meta.customer_groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}</select></Field>
          </div>
          <Field label="Коментар" hint="Бачать менеджери в картці замовлення"><textarea rows={3} value={v("comment", "")} onChange={(e) => setF({ ...f, comment: e.target.value })} /></Field>
          <div className={`cu-bl ${bl ? "on" : ""}`}>
            <label className="check"><input type="checkbox" checked={bl} onChange={(e) => setF({ ...f, blacklisted: e.target.checked })} /> <Ban size={15} /> Чорний список</label>
            {bl && <input value={v("blacklist_reason", "")} onChange={(e) => setF({ ...f, blacklist_reason: e.target.value })} placeholder="Причина, наприклад «не забирає посилки»" />}
            <span className="hint">{bl ? "У нових замовленнях від цього покупця менеджер побачить попередження." : <><ShieldCheck size={13} /> Замовлення від покупця приймаються без попереджень.</>}</span>
          </div>
          <div className="form-actions"><button className="btn primary" disabled={!dirty || save.isPending}>Зберегти</button>
            {dirty && <button type="button" className="btn ghost" onClick={() => setF({})}>Скасувати зміни</button>}</div>
        </form>
        <div>
          <h3>Історія замовлень</h3>
          {data.history.length ? (
            <table className="t dense"><tbody>{data.history.map((o) => (
              <tr key={o.id} className="clickable" onClick={() => nav(`/orders/${o.id}`)}>
                <td><b>№{o.id}</b><span className="sub">{date(o.created_at)}</span></td>
                <td className="ell" style={{ maxWidth: 220 }}>{o.items.map((i) => (i.qty > 1 ? `${i.name} ×${i.qty}` : i.name)).join(", ")}</td>
                <td className="num">{money(o.total)} ₴</td><td><Pill status={statuses[o.status_id]} /></td>
              </tr>
            ))}</tbody></table>
          ) : <p className="hint">Замовлень ще немає.</p>}
        </div>
      </div>
    </Modal>
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
        <Field label="Телефон"><input value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} inputMode="tel" required autoFocus placeholder="+380…" /></Field>
        <Field label="Ім'я"><input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
        <Field label="Email"><input type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
        <Field label="Група"><select value={f.group_id} onChange={(e) => setF({ ...f, group_id: e.target.value ? Number(e.target.value) : "" })}>
          <option value="">за замовчуванням</option>{meta.customer_groups.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}</select></Field>
        <div className="form-actions"><button className="btn primary" disabled={create.isPending}>Додати покупця</button><button type="button" className="btn" onClick={onClose}>Скасувати</button></div>
      </form>
    </Modal>
  );
}
