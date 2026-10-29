import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Truck } from "lucide-react";
import { api, qs } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { date, dt, money, num } from "../lib/format";
import type { Move, Product, Purchase, Supplier } from "../lib/types";
import { Badge, Empty, Field, Kpi, Modal, Spinner } from "../components/ui";

const canEditStock = (role: string) => role === "admin" || role === "warehouse";

// ================================================================ товари
export function ProductsPage() {
  const meta = useMeta();
  const [q, setQ] = useState("");
  const [show, setShow] = useState("active");
  const [edit, setEdit] = useState<number | "new" | null>(null);
  const dq = useDebounced(q, 250);
  const { data, isLoading } = useQuery({ queryKey: ["products", dq, show], queryFn: () => api.get<Product[]>(`/products${qs({ q: dq, show })}`) });
  const editable = canEditStock(meta.user.role);

  return (
    <div>
      <div className="head"><h1>Товари <small className="muted">{data?.length ?? ""}</small></h1>
        <div className="actions">{editable && <button className="btn primary" onClick={() => setEdit("new")}><Plus size={15} /> Товар</button>}</div></div>
      <div className="filters">
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Назва або артикул" />
        <select value={show} onChange={(e) => setShow(e.target.value)}><option value="active">Активні</option><option value="inactive">Архів</option><option value="all">Усі</option></select>
      </div>
      <div className="card flush tablewrap">
        <table className="t dense">
          <thead><tr><th>Назва</th><th>Артикул</th><th className="num">Ціна</th><th className="num">Собівартість</th><th className="num">Маржа</th><th className="num">На складі</th><th className="num">Резерв</th><th className="num">Доступно</th></tr></thead>
          <tbody>
            {isLoading && <tr><td colSpan={8}><Empty><Spinner /></Empty></td></tr>}
            {data?.map((p) => (
              <tr key={p.id} className="clickable" onClick={() => setEdit(p.id)}>
                <td>{p.name} {p.upsell && <Badge kind="info">апсел</Badge>} {!p.active && <Badge>архів</Badge>}</td>
                <td className="mono">{p.sku}</td><td className="num">{money(p.price, true)}</td><td className="num">{money(p.cost, true)}</td>
                <td className="num">{money(p.price - p.cost, true)}</td><td className="num">{p.stock}</td><td className="num">{p.reserved}</td>
                <td className={`num ${p.available <= p.min_stock ? "lowstock" : ""}`}>{p.available}</td>
              </tr>
            ))}
            {data && !data.length && <tr><td colSpan={8}><Empty>Товарів немає</Empty></td></tr>}
          </tbody>
        </table>
      </div>
      {edit !== null && <ProductModal id={edit} editable={editable} onClose={() => setEdit(null)} />}
    </div>
  );
}

function ProductModal({ id, editable, onClose }: { id: number | "new"; editable: boolean; onClose: () => void }) {
  const isNew = id === "new";
  const qc = useQueryClient();
  const toast = useToast();
  const { data } = useQuery({ queryKey: ["products", "one", id], queryFn: () => api.get<Product & { moves: Move[]; sold: number }>(`/products/${id}`), enabled: !isNew });
  const [f, setF] = useState<Record<string, string | boolean>>({});
  const v = (k: string, d: string | boolean = "") => (k in f ? f[k] : data ? (data as unknown as Record<string, string | boolean>)[k] ?? d : d);
  const save = useMutation({
    mutationFn: () => {
      const body = { name: v("name"), sku: v("sku"), price: v("price", "0"), cost: v("cost", "0"), weight: v("weight", "0.5"),
        min_stock: v("min_stock", "0"), upsell: !!v("upsell", false), active: !!v("active", true), initial_stock: f.initial_stock };
      return isNew ? api.post<Product>("/products", body) : api.patch<Product>(`/products/${id}`, body);
    },
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["products"] }); qc.invalidateQueries({ queryKey: ["meta"] }); toast("Збережено"); onClose(); },
    onError: (e) => toast(errText(e), "error"),
  });
  if (!isNew && !data) return <Modal onClose={onClose}><Empty><Spinner /></Empty></Modal>;
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.type === "checkbox" ? e.target.checked : e.target.value });

  return (
    <Modal onClose={onClose} title={isNew ? "Новий товар" : String(v("name"))}>
      <div className="grid half">
        <form className="form" onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
          <fieldset disabled={!editable} style={{ border: 0, padding: 0, margin: 0 }}>
            <Field label="Назва"><input value={String(v("name"))} onChange={set("name")} required autoFocus={isNew} /></Field>
            <div className="row">
              <Field label="Артикул (SKU)" hint="Для прийому заявок з лендингу"><input className="mono" value={String(v("sku"))} onChange={set("sku")} /></Field>
              <Field label="Вага, кг"><input value={String(v("weight", "0.5"))} onChange={set("weight")} inputMode="decimal" /></Field>
            </div>
            <div className="row">
              <Field label="Ціна продажу, грн"><input value={String(v("price", ""))} onChange={set("price")} inputMode="decimal" required /></Field>
              <Field label="Собівартість, грн" hint="Середня, оновлюється при оприбуткуванні"><input value={String(v("cost", ""))} onChange={set("cost")} inputMode="decimal" /></Field>
            </div>
            <div className="row">
              {isNew && <Field label="Початковий залишок, шт"><input type="number" value={String(f.initial_stock ?? "0")} onChange={set("initial_stock")} /></Field>}
              <Field label="Мінімальний залишок" hint="Нижче — підсвічується"><input type="number" value={String(v("min_stock", "0"))} onChange={set("min_stock")} /></Field>
            </div>
            <label className="check mt"><input type="checkbox" checked={!!v("upsell", false)} onChange={set("upsell")} /> Товар для допродажу (апсел)</label>
            <label className="check"><input type="checkbox" checked={!!v("active", true)} onChange={set("active")} /> Активний (показується в замовленнях)</label>
            {editable && <button className="btn primary mt" disabled={save.isPending}>Зберегти</button>}
          </fieldset>
        </form>
        {data && (
          <div className="stack">
            <div className="kpis" style={{ margin: 0 }}>
              <Kpi label="На складі" value={data.stock} /><Kpi label="Резерв" value={data.reserved} />
              <Kpi label="Доступно" value={<span className={data.available <= data.min_stock ? "lowstock" : ""}>{data.available}</span>} />
            </div>
            <MovesTable moves={data.moves} compact />
          </div>
        )}
      </div>
    </Modal>
  );
}

function MovesTable({ moves, compact = false }: { moves: Move[]; compact?: boolean }) {
  return (
    <div className="card flush tablewrap">
      <table className="t dense">
        <thead><tr><th>Дата</th>{!compact && <th>Товар</th>}<th>Операція</th><th className="num">Склад</th><th className="num">Резерв</th>{!compact && <th>Хто</th>}</tr></thead>
        <tbody>
          {moves.map((m) => (
            <tr key={m.id}><td className="nowrap">{dt(m.created_at, true)}</td>{!compact && <td>{m.product}</td>}
              <td>{m.kind_name} {m.order_id && <span className="muted">№{m.order_id}</span>}{m.purchase_id && <span className="muted"> закупівля №{m.purchase_id}</span>}{m.comment && <span className="sub">{m.comment}</span>}</td>
              <td className="num">{m.stock_delta ? (m.stock_delta > 0 ? `+${m.stock_delta}` : m.stock_delta) : ""}</td>
              <td className="num">{m.reserved_delta ? (m.reserved_delta > 0 ? `+${m.reserved_delta}` : m.reserved_delta) : ""}</td>
              {!compact && <td>{m.user}</td>}</tr>
          ))}
          {!moves.length && <tr><td colSpan={6}><Empty>Руху ще не було</Empty></td></tr>}
        </tbody>
      </table>
    </div>
  );
}

// ================================================================ склад
export function WarehousePage() {
  const qc = useQueryClient();
  const toast = useToast();
  const [product, setProduct] = useState(0);
  const [kind, setKind] = useState("");
  const [lowOnly, setLowOnly] = useState(false);
  const [adj, setAdj] = useState({ product_id: "", mode: "set", qty: "", comment: "" });
  const { data } = useQuery({ queryKey: ["warehouse", product, kind], queryFn: () => api.get<{ products: Product[]; value: number; units: number; reserved: number; low: number; moves: Move[]; kinds: Record<string, string> }>(`/warehouse${qs({ product, kind })}`) });
  const adjust = useMutation({
    mutationFn: () => api.post<Product>("/warehouse/adjust", adj),
    onSuccess: (p) => { toast(`Залишок «${p.name}»: ${p.stock}`); setAdj({ ...adj, qty: "", comment: "" }); qc.invalidateQueries({ queryKey: ["warehouse"] }); qc.invalidateQueries({ queryKey: ["products"] }); },
    onError: (e) => toast(errText(e), "error"),
  });
  if (!data) return <Empty><Spinner /></Empty>;
  const list = lowOnly ? data.products.filter((p) => p.available <= p.min_stock) : data.products;
  return (
    <div>
      <div className="head"><h1>Склад</h1></div>
      <div className="kpis">
        <Kpi label="Одиниць на складі" value={data.units} /><Kpi label="У резерві" value={data.reserved} />
        <Kpi label="Вартість залишків" value={`${money(data.value)} ₴`} sub="за собівартістю" />
        <Kpi label="Закінчуються" value={<span className={data.low ? "lowstock" : ""}>{data.low}</span>} sub={<a onClick={() => setLowOnly(!lowOnly)}>{lowOnly ? "показати всі" : "показати"}</a>} />
      </div>
      <div className="grid two">
        <div className="card flush tablewrap">
          <table className="t dense">
            <thead><tr><th>Товар</th><th className="num">На складі</th><th className="num">Резерв</th><th className="num">Доступно</th><th className="num">Мін.</th><th className="num">Вартість</th></tr></thead>
            <tbody>{list.map((p) => (
              <tr key={p.id} className={`clickable ${product === p.id ? "sel-on" : ""}`} onClick={() => { setProduct(product === p.id ? 0 : p.id); setAdj({ ...adj, product_id: String(p.id) }); }}>
                <td>{p.name}{p.sku && <span className="sub mono">{p.sku}</span>}</td><td className="num">{p.stock}</td><td className="num">{p.reserved}</td>
                <td className={`num ${p.available <= p.min_stock ? "lowstock" : ""}`}>{p.available}</td><td className="num muted">{p.min_stock}</td>
                <td className="num">{money(p.cost * Math.max(p.stock, 0))}</td></tr>
            ))}</tbody>
          </table>
        </div>
        <form className="card form" onSubmit={(e) => { e.preventDefault(); adjust.mutate(); }}>
          <h2>Коригування / інвентаризація</h2>
          <Field label="Товар"><select value={adj.product_id} onChange={(e) => setAdj({ ...adj, product_id: e.target.value })} required>
            <option value="">Оберіть товар…</option>{data.products.map((p) => <option key={p.id} value={p.id}>{p.name} (зараз {p.stock})</option>)}</select></Field>
          <div className="row">
            <Field label="Режим"><select value={adj.mode} onChange={(e) => setAdj({ ...adj, mode: e.target.value })}><option value="set">Встановити фактичний залишок</option><option value="delta">Додати / відняти (+5, −2)</option></select></Field>
            <Field label="Кількість"><input value={adj.qty} onChange={(e) => setAdj({ ...adj, qty: e.target.value })} required inputMode="numeric" /></Field>
          </div>
          <Field label="Причина"><input value={adj.comment} onChange={(e) => setAdj({ ...adj, comment: e.target.value })} placeholder="Інвентаризація, брак, пересорт…" /></Field>
          <button className="btn primary mt" disabled={adjust.isPending}>Застосувати</button>
        </form>
      </div>
      <div className="head mt"><h2 style={{ margin: 0 }}>Рух товарів {product ? `· ${data.products.find((p) => p.id === product)?.name ?? ""}` : ""}</h2>
        <select style={{ width: "auto" }} value={kind} onChange={(e) => setKind(e.target.value)}><option value="">Усі операції</option>{Object.entries(data.kinds).map(([k, n]) => <option key={k} value={k}>{n}</option>)}</select></div>
      <MovesTable moves={data.moves} />
    </div>
  );
}

// ================================================================ закупівлі
const PSTATUS: Record<string, [string, "" | "ok" | "bad" | "info"]> = { draft: ["Чернетка", ""], ordered: ["Замовлено", "info"], received: ["Оприбутковано", "ok"], cancelled: ["Скасовано", "bad"] };

export function PurchasesPage() {
  const [status, setStatus] = useState("");
  const [open, setOpen] = useState<number | "new" | null>(null);
  const [suppliers, setSuppliers] = useState(false);
  const { data } = useQuery({ queryKey: ["purchases", status], queryFn: () => api.get<Purchase[]>(`/purchases${qs({ status })}`) });
  return (
    <div>
      <div className="head"><h1>Закупівлі</h1>
        <div className="actions"><button className="btn ghost" onClick={() => setSuppliers(true)}><Truck size={15} /> Постачальники</button>
          <button className="btn primary" onClick={() => setOpen("new")}><Plus size={15} /> Закупівля</button></div></div>
      <div className="tabs">
        <a className={!status ? "on" : ""} onClick={() => setStatus("")}>Усі</a>
        {Object.entries(PSTATUS).map(([k, [n]]) => <a key={k} className={status === k ? "on" : ""} onClick={() => setStatus(k)}>{n}</a>)}
      </div>
      <div className="card flush tablewrap">
        <table className="t dense">
          <thead><tr><th>№</th><th>Дата</th><th>Постачальник</th><th>Товари</th><th className="num">Сума</th><th>Статус</th></tr></thead>
          <tbody>
            {data?.map((p) => (
              <tr key={p.id} className="clickable" onClick={() => setOpen(p.id)}>
                <td><b>{p.id}</b></td><td>{date(p.created_at)}{p.received_at && <span className="sub">отримано {date(p.received_at)}</span>}</td>
                <td>{p.supplier || "—"}</td><td className="ell">{p.items.map((i) => `${i.name} ×${i.qty}`).join(", ")}</td>
                <td className="num">{money(p.total)}</td><td><Badge kind={PSTATUS[p.status]?.[1]}>{PSTATUS[p.status]?.[0]}</Badge></td></tr>
            ))}
            {data && !data.length && <tr><td colSpan={6}><Empty>Закупівель ще немає</Empty></td></tr>}
          </tbody>
        </table>
      </div>
      {open !== null && <PurchaseModal id={open} onClose={() => setOpen(null)} />}
      {suppliers && <SuppliersModal onClose={() => setSuppliers(false)} />}
    </div>
  );
}

function PurchaseModal({ id, onClose }: { id: number | "new"; onClose: () => void }) {
  const meta = useMeta();
  const qc = useQueryClient();
  const toast = useToast();
  const isNew = id === "new";
  const { data } = useQuery({ queryKey: ["purchases", "one", id], queryFn: () => api.get<Purchase>(`/purchases/${id}`), enabled: !isNew });
  const { data: sups = [] } = useQuery({ queryKey: ["suppliers"], queryFn: () => api.get<Supplier[]>("/suppliers") });
  const [draft, setDraft] = useState<{ supplier_id: string; comment: string; items: { product_id: string; qty: string; cost: string }[] } | null>(null);
  const cur = draft ?? (data ? { supplier_id: String(data.supplier_id ?? ""), comment: data.comment, items: data.items.map((i) => ({ product_id: String(i.product_id), qty: String(i.qty), cost: String(i.cost) })) }
    : { supplier_id: "", comment: "", items: [{ product_id: "", qty: "1", cost: "" }] });
  const editable = isNew || (data && (data.status === "draft" || data.status === "ordered"));
  const total = cur.items.reduce((s, i) => s + num(i.qty) * num(i.cost), 0);
  const productsById = useMemo(() => Object.fromEntries(meta.products.map((p) => [String(p.id), p])), [meta.products]);
  const run = useMutation({
    mutationFn: (then: string) => isNew ? api.post<Purchase>("/purchases", { ...cur, then }) : api.patch<Purchase>(`/purchases/${id}`, { ...cur, then }),
    onSuccess: (_p, then) => {
      toast(then === "receive" ? "Товар оприбутковано, залишки оновлено" : then === "cancel" ? "Закупівлю скасовано" : "Збережено");
      qc.invalidateQueries({ queryKey: ["purchases"] }); qc.invalidateQueries({ queryKey: ["products"] }); qc.invalidateQueries({ queryKey: ["warehouse"] }); qc.invalidateQueries({ queryKey: ["meta"] });
      onClose();
    },
    onError: (e) => toast(errText(e), "error"),
  });
  const setItem = (i: number, patch: Partial<{ product_id: string; qty: string; cost: string }>) => {
    const items = cur.items.map((x, j) => (j === i ? { ...x, ...patch } : x));
    if (patch.product_id && !items[i].cost) items[i].cost = String(productsById[patch.product_id]?.cost || "");
    setDraft({ ...cur, items });
  };
  if (!isNew && !data) return <Modal onClose={onClose}><Empty><Spinner /></Empty></Modal>;
  return (
    <Modal onClose={onClose} title={isNew ? "Нова закупівля" : <>Закупівля №{id} <Badge kind={PSTATUS[data!.status]?.[1]}>{PSTATUS[data!.status]?.[0]}</Badge></>}>
      <fieldset disabled={!editable} className="form" style={{ border: 0, padding: 0, margin: 0 }}>
        <div className="row">
          <Field label="Постачальник"><select value={cur.supplier_id} onChange={(e) => setDraft({ ...cur, supplier_id: e.target.value })}><option value="">—</option>{sups.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}</select></Field>
          <Field label="Коментар"><input value={cur.comment} onChange={(e) => setDraft({ ...cur, comment: e.target.value })} /></Field>
        </div>
        <table className="t items mt">
          <thead><tr><th>Товар</th><th className="num">К-сть</th><th className="num">Ціна закупівлі</th><th className="num">Сума</th><th /></tr></thead>
          <tbody>{cur.items.map((it, i) => (
            <tr key={i}>
              <td><select value={it.product_id} onChange={(e) => setItem(i, { product_id: e.target.value })}><option value="">Оберіть…</option>{meta.products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></td>
              <td className="qty num"><input type="number" min={1} value={it.qty} onChange={(e) => setItem(i, { qty: e.target.value })} /></td>
              <td className="price num"><input value={it.cost} onChange={(e) => setItem(i, { cost: e.target.value })} inputMode="decimal" /></td>
              <td className="num">{money(num(it.qty) * num(it.cost), true)}</td>
              <td><button type="button" className="x" onClick={() => setDraft({ ...cur, items: cur.items.filter((_, j) => j !== i) })}>×</button></td>
            </tr>
          ))}</tbody>
          <tfoot><tr><td colSpan={3}>Разом</td><td className="num">{money(total, true)}</td><td /></tr></tfoot>
        </table>
        {editable && <>
          <button type="button" className="btn sm mt" onClick={() => setDraft({ ...cur, items: [...cur.items, { product_id: "", qty: "1", cost: "" }] })}><Plus size={14} /> Рядок</button>
          <div className="row mt">
            <button className="btn" onClick={() => run.mutate("save")}>Зберегти</button>
            {(isNew || data?.status === "draft") && <button className="btn" onClick={() => run.mutate("ordered")}>Позначити «Замовлено»</button>}
            <button className="btn primary" onClick={() => { if (window.confirm("Оприбуткувати товар? Залишки на складі збільшаться.")) run.mutate("receive"); }}>Оприбуткувати на склад</button>
            {!isNew && <><span className="spacer" /><button className="btn danger" onClick={() => { if (window.confirm("Скасувати закупівлю?")) run.mutate("cancel"); }}>Скасувати</button></>}
          </div>
        </>}
      </fieldset>
    </Modal>
  );
}

function SuppliersModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const toast = useToast();
  const { data = [] } = useQuery({ queryKey: ["suppliers"], queryFn: () => api.get<Supplier[]>("/suppliers") });
  const [nw, setNw] = useState({ name: "", phone: "", comment: "" });
  const save = useMutation({
    mutationFn: (s: Partial<Supplier>) => api.post<Supplier>("/suppliers", s),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["suppliers"] }); toast("Збережено"); setNw({ name: "", phone: "", comment: "" }); },
    onError: (e) => toast(errText(e), "error"),
  });
  return (
    <Modal onClose={onClose} title="Постачальники">
      <div className="stack">
        {data.map((s) => <SupplierRow key={s.id} s={s} onSave={(x) => save.mutate(x)} />)}
        <form className="row" onSubmit={(e) => { e.preventDefault(); save.mutate(nw); }}>
          <input placeholder="Назва нового постачальника" value={nw.name} onChange={(e) => setNw({ ...nw, name: e.target.value })} required style={{ flex: 2 }} />
          <input placeholder="Телефон" value={nw.phone} onChange={(e) => setNw({ ...nw, phone: e.target.value })} style={{ flex: 1 }} />
          <button className="btn primary">Додати</button>
        </form>
      </div>
    </Modal>
  );
}

function SupplierRow({ s, onSave }: { s: Supplier; onSave: (s: Supplier) => void }) {
  const [v, setV] = useState(s);
  return (
    <form className="row" onSubmit={(e) => { e.preventDefault(); onSave(v); }}>
      <input value={v.name} onChange={(e) => setV({ ...v, name: e.target.value })} style={{ flex: 2 }} />
      <input value={v.phone} onChange={(e) => setV({ ...v, phone: e.target.value })} style={{ flex: 1 }} />
      <input value={v.comment} onChange={(e) => setV({ ...v, comment: e.target.value })} placeholder="Коментар" style={{ flex: 2 }} />
      <button className="btn sm">Зберегти</button>
    </form>
  );
}
