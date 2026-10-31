// Товари: список з фото й фільтрами; вікно товару в три колонки (UI-DESIGN §7, макет 10): основне й опис · ціни, склад, доставка · варіанти, допродаж, продажі;
// довідники каталогу — категорії (два рівні), виробники, атрибути для варіантів.
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Archive, BadgeCheck, Boxes, Check, ChevronLeft, ChevronRight, Copy, Factory, FolderTree, Globe, GripVertical, ImagePlus, MoreHorizontal, Package, Plus, Tags, Trash2, Wand2, X,
} from "lucide-react";
import { api, qs, ROOT } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { money, num } from "../lib/format";
import type { AttributeGroup, Category, Manufacturer, Product, ProductDetail } from "../lib/types";
type ProductSummary = { days: number; qty: number; sum: number; margin: number; buyout_rate: number | null; upsell_share: number | null; orders: number; sold_total: number };
import { Badge, Block, Button, confirmAction, Empty, Field, IconButton, MenuButton, MobileActs, Modal, RoundButton, Spinner, Tag, Toggle, Window, useMobile , Select } from "../components/ui";
import MultiSelect from "../components/MultiSelect";
import { MovesTable } from "./Catalog";
import "./products.css";

const canEdit = (role: string) => role === "admin" || role === "warehouse";
const TABS: [string, string, typeof Package][] = [["products", "Товари", Package], ["categories", "Категорії", FolderTree],
  ["manufacturers", "Виробники", Factory], ["attributes", "Атрибути", Tags]];

export default function ProductsPage() {
  const meta = useMeta();
  const [sp, setSp] = useSearchParams();
  const tab = sp.get("tab") || "products";
  const editable = canEdit(meta.user.role);
  return (
    <div className="products">
      <div className="head">
        <h1><span className="h-ico"><Package size={18} /></span>Товари</h1>
      </div>
      <div className="tabs">
        {TABS.filter(([k]) => k === "products" || editable).map(([k, label, Icon]) => (
          <a key={k} className={tab === k ? "on" : ""} onClick={() => setSp(k === "products" ? {} : { tab: k })}><Icon size={15} /> {label}</a>
        ))}
      </div>
      {tab === "products" && <ProductList editable={editable} />}
      {tab === "categories" && <CategoriesTab />}
      {tab === "manufacturers" && <ManufacturersTab />}
      {tab === "attributes" && <AttributesTab />}
    </div>
  );
}

// ---------------------------------------------------------------- список товарів
function categoryOptions(cats: { id: number; name: string; parent_id: number | null }[]) {
  const roots = cats.filter((c) => !c.parent_id);
  const out: { id: number; label: string; depth: number }[] = [];
  for (const r of roots) {
    out.push({ id: r.id, label: r.name, depth: 0 });
    for (const c of cats.filter((x) => x.parent_id === r.id)) out.push({ id: c.id, label: c.name, depth: 1 });
  }
  for (const c of cats.filter((x) => x.parent_id && !roots.some((r) => r.id === x.parent_id))) out.push({ id: c.id, label: c.name, depth: 0 });
  return out;
}

function ProductList({ editable }: { editable: boolean }) {
  const meta = useMeta();
  const [sp, setSp] = useSearchParams();
  const [q, setQ] = useState("");
  const [show, setShow] = useState("active");
  const [category, setCategory] = useState("");
  const [manufacturer, setManufacturer] = useState("");
  const [stockState, setStockState] = useState("");
  const [edit, setEdit] = useState<number | "new" | null>(sp.get("new") ? "new" : null);
  useEffect(() => {
    const open = sp.get("open");
    if (sp.get("new") || open) {
      setEdit(open ? Number(open) : "new");
      const n = new URLSearchParams(sp); n.delete("new"); n.delete("open"); setSp(n, { replace: true });
    }
  }, [sp, setSp]);
  const dq = useDebounced(q, 250);
  const params = { q: dq, show, category, manufacturer, stock_state: stockState };
  const { data, isLoading } = useQuery({ queryKey: ["products", params], queryFn: () => api.get<Product[]>(`/products${qs(params)}`) });
  const cats = useMemo(() => Object.fromEntries(meta.categories.map((c) => [c.id, c.name])), [meta.categories]);
  const brands = useMemo(() => Object.fromEntries(meta.manufacturers.map((m) => [m.id, m.name])), [meta.manufacturers]);
  const catOpts = categoryOptions(meta.categories);
  const mobile = useMobile();

  return (
    <>
      {editable && <MobileActs><RoundButton icon={Plus} label="Новий товар" primary onClick={() => setEdit("new")} /></MobileActs>}
      <div className="filters">
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Назва, артикул або модель" />
        {catOpts.length > 0 && <Select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">Усі категорії</option><option value="-1">Без категорії</option>
          {catOpts.map((c) => <option key={c.id} value={c.id}>{c.depth ? "  · " : ""}{c.label}</option>)}</Select>}
        {meta.manufacturers.length > 0 && <Select value={manufacturer} onChange={(e) => setManufacturer(e.target.value)}>
          <option value="">Усі виробники</option>{meta.manufacturers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</Select>}
        <Select value={stockState} onChange={(e) => setStockState(e.target.value)}>
          <option value="">Будь-який залишок</option><option value="in">Є в наявності</option><option value="low">Закінчується</option>
          <option value="out">Немає</option><option value="minus">Мінус</option></Select>
        <Select value={show} onChange={(e) => setShow(e.target.value)}><option value="active">Активні</option><option value="inactive">Архів</option><option value="all">Усі</option></Select>
        <span className="spacer" />
        {editable && <button className="btn primary" onClick={() => setEdit("new")}><Plus size={15} /> Товар</button>}
      </div>
      {mobile && (
        <div className="pr-mlist">
          {isLoading && <div className="m-card m-skel" aria-hidden><i /><i /><i /></div>}
          {data?.map((p) => {
            const st = !p.active ? ["архів", "#7C7B76"] : p.upsell ? ["допродаж", "#7C3AED"] : p.available <= 0 ? ["немає", "#DC2626"]
              : p.available <= p.min_stock ? ["закінчується", "#D97706"] : ["у продажу", "#16A34A"];
            const sale = p.discount_percent > 0 ? p.sale_price : p.price;
            const mPct = sale > 0 && p.cost > 0 ? Math.round(((sale - p.cost) / sale) * 100) : null;
            return (
              <button key={p.id} type="button" className="pr-mrow" onClick={() => setEdit(p.id)}>
                <span className="mc-thumb l">{p.photo ? <img src={`${ROOT}${p.photo}`} alt="" loading="lazy" /> : <Package size={20} />}</span>
                <span className="pr-mt">
                  <span className="pill" style={{ ["--c" as string]: st[1] }}>{st[0]}</span>
                  <b className="ell">{p.name}</b>
                  <small><b>{money(sale)} ₴</b> · {p.available} шт{mPct != null ? ` · маржа ${mPct}%` : ""}</small>
                </span>
                <ChevronRight size={18} className="pr-mgo" />
              </button>
            );
          })}
          {data && !data.length && <Empty><Package size={22} className="e-ico" />{dq || category || manufacturer || stockState ? "За цими фільтрами товарів немає" : "Додайте перший товар"}</Empty>}
        </div>
      )}
      {!mobile && <div className="card flush tablewrap">
        <table className="t pr-table m-cards">
          <thead><tr><th>Товар</th><th>Категорія</th><th>Артикул</th><th className="num">Ціна</th><th className="num">Собівартість</th>
            <th className="num">Маржа</th><th className="num">Доступно</th><th className="num">Резерв</th></tr></thead>
          <tbody>
            {isLoading && <tr><td colSpan={8}><Empty><Spinner /></Empty></td></tr>}
            {data?.map((p) => {
              const active = (p.variants ?? []).filter((v) => v.active);
              return (
                <tr key={p.id} className="clickable" onClick={() => setEdit(p.id)}>
                  <td><div className="pr-cell">
                    {p.photo ? <img src={`${ROOT}${p.photo}`} alt="" loading="lazy" /> : <span className="pr-ph"><Package size={16} /></span>}
                    <div><div className="pr-name">{p.name}</div>
                      <div className="pr-tags">{p.manufacturer_id && <span>{brands[p.manufacturer_id]}{p.model && ` ${p.model}`}</span>}
                        {active.length > 0 && <Badge>{active.length} варіант{active.length === 1 ? "" : active.length < 5 ? "и" : "ів"}</Badge>}
                        {p.upsell && <Badge kind="info">допродаж</Badge>}{!p.active && <Badge>архів</Badge>}</div></div>
                  </div></td>
                  <td className="muted">{p.category_id ? cats[p.category_id] ?? "" : ""}</td>
                  <td className="mono">{p.sku}</td>
                  <td className="num">{p.discount_percent > 0 ? <><span className="pr-old">{money(p.price)}</span> <b className="pr-sale">{money(p.sale_price)}</b></> : money(p.price)}</td>
                  <td className="num muted">{money(p.cost)}</td>
                  <td className="num">{money(p.sale_price - p.cost)}</td>
                  <td className={`num ${p.available <= p.min_stock ? "lowstock" : ""}`}><b>{p.available}</b></td>
                  <td className="num muted">{p.reserved || ""}</td>
                </tr>
              );
            })}
            {data && !data.length && <tr><td colSpan={8}><Empty><Package size={22} className="e-ico" />{dq || category || manufacturer || stockState ? "За цими фільтрами товарів немає" : "Додайте перший товар — кнопка «Товар» праворуч угорі"}</Empty></td></tr>}
          </tbody>
        </table>
      </div>}
      {edit !== null && <ProductModal id={edit} editable={editable} onClose={() => setEdit(null)} onCreated={(id) => setEdit(id)} />}
    </>
  );
}

// ---------------------------------------------------------------- картка товару
type VRow = { id?: number; name: string; sku: string; attribute_ids: number[]; price: string; active: boolean; initial_stock: string; stock?: number; reserved?: number };

function ProductModal({ id, editable, onClose, onCreated }: { id: number | "new"; editable: boolean; onClose: () => void; onCreated: (id: number) => void }) {
  const mobile = useMobile();
  const isNew = id === "new";
  const qc = useQueryClient();
  const toast = useToast();
  const meta = useMeta();
  const { data } = useQuery({ queryKey: ["products", "one", id], queryFn: () => api.get<ProductDetail>(`/products/${id}`), enabled: !isNew });
  const [showMoves, setShowMoves] = useState(false);
  const [offerWith, setOfferWith] = useState<number[] | null>(null);
  const [f, setF] = useState<Record<string, unknown>>({});
  const [variants, setVariants] = useState<VRow[] | null>(null);
  const [pending, setPending] = useState<File[]>([]);
  const v = <T,>(k: string, d: T): T => (k in f ? (f[k] as T) : data ? ((data as unknown as Record<string, T>)[k] ?? d) : d);
  const curVariants: VRow[] = variants ?? (data?.variants ?? []).map((x) => ({ id: x.id, name: x.name, sku: x.sku, attribute_ids: x.attribute_ids,
    price: x.price == null ? "" : String(x.price), active: x.active, initial_stock: "", stock: x.stock, reserved: x.reserved }));
  const [upsellFor, setUpsellFor] = useState<number[] | null>(null);
  const curFor = upsellFor ?? data?.upsell_for ?? [];
  const mains = meta.products.filter((p) => !p.upsell && p.id !== (isNew ? 0 : id));
  const refresh = () => { qc.invalidateQueries({ queryKey: ["products"] }); qc.invalidateQueries({ queryKey: ["meta"] }); };

  const upload = async (pid: number, files: File[]) => {
    if (!files.length) return;
    const fd = new FormData();
    files.forEach((x) => fd.append("files", x));
    await api.post(`/products/${pid}/photos`, fd);
  };
  const save = useMutation({
    mutationFn: async () => {
      const n = (k: string, d = "0") => String(v(k, d) ?? d);
      const body: Record<string, unknown> = {
        name: v("name", ""), sku: v("sku", ""), price: n("price"), cost: n("cost"), weight: n("weight", "0.5"), min_stock: n("min_stock"),
        length: num(v("length", 0)), width: num(v("width", 0)), height: num(v("height", 0)), ship_description: String(v("ship_description", "")),
        warranty_months: Math.max(0, Math.round(num(v("warranty_months", 0)))),
        upsell: !!v("upsell", false), upsell_for: curFor, active: !!v("active", true), category_id: v<number | null>("category_id", null) || null,
        manufacturer_id: v<number | null>("manufacturer_id", null) || null, model: String(v("model", "")), description: String(v("description", "")),
        countries: v<string[]>("countries", []), spec_price: n("spec_price"), wholesale_price: n("wholesale_price"),
      };
      if (isNew) body.initial_stock = f.initial_stock;
      if (variants !== null) body.variants = variants.map((x) => ({ id: x.id, name: x.name, sku: x.sku, attribute_ids: x.attribute_ids,
        price: x.price === "" ? null : x.price, active: x.active, initial_stock: Number(x.initial_stock) || 0 }));
      const p = isNew ? await api.post<Product>("/products", body) : await api.patch<Product>(`/products/${id}`, body);
      await upload(p.id, pending);
      return p;
    },
    onSuccess: (p) => { refresh(); toast(isNew ? "Товар створено" : "Збережено"); setPending([]); setVariants(null); setF({});
      if (isNew) onCreated(p.id); else qc.invalidateQueries({ queryKey: ["products", "one", id] }); },
    onError: (e) => toast(errText(e), "error"),
  });
  const del = useMutation({
    mutationFn: () => api.del<{ deleted: boolean; message: string }>(`/products/${id}`),
    onSuccess: (r) => { refresh(); toast(r.message, r.deleted ? "ok" : "warn"); onClose(); },
    onError: (e) => toast(errText(e), "error"),
  });
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setF({ ...f, [k]: e.target instanceof HTMLInputElement && e.target.type === "checkbox" ? e.target.checked : e.target.value });
  const price = num(v("price", 0)), spec = num(v("spec_price", 0)), cost = num(v("cost", 0));
  const sale = spec > 0 ? spec : price;

  const sold = useQuery({ queryKey: ["products", "summary", id], queryFn: () => api.get<ProductSummary>(`/products/${id}/summary?days=30`), enabled: !isNew });
  const offerInit = isNew ? [] : meta.products.filter((p) => p.upsell && (p.upsell_for ?? []).includes(id as number)).map((p) => p.id);
  const offers = offerWith ?? offerInit;
  const upsellPool = meta.products.filter((p) => p.id !== (isNew ? 0 : id));
  const saveAll = async () => {
    const p = await save.mutateAsync();
    if (offerWith && !isNew) {  // «Пропонувати разом з цим товаром»: оновити список «до яких товарів» у самих допродажів
      const add = offerWith.filter((x) => !offerInit.includes(x)), rm = offerInit.filter((x) => !offerWith.includes(x));
      for (const pid of [...add, ...rm]) {
        const up = meta.products.find((x) => x.id === pid);
        if (!up) continue;
        const list = add.includes(pid) ? [...new Set([...(up.upsell_for ?? []), p.id])] : (up.upsell_for ?? []).filter((x) => x !== p.id);
        await api.patch(`/products/${pid}`, { upsell: true, upsell_for: list });
      }
      setOfferWith(null);
      refresh();
    }
  };
  const duplicate = useMutation({
    mutationFn: async () => api.post<Product>("/products", { name: `${v("name", "")} (копія)`, sku: "", price: String(v("price", "0")), cost: String(v("cost", "0")),
      weight: String(v("weight", "0.5")), min_stock: String(v("min_stock", "0")), category_id: v<number | null>("category_id", null) || null,
      manufacturer_id: v<number | null>("manufacturer_id", null) || null, model: String(v("model", "")), description: String(v("description", "")),
      countries: v<string[]>("countries", []), spec_price: String(v("spec_price", "0")), wholesale_price: String(v("wholesale_price", "0")),
      length: num(v("length", 0)), width: num(v("width", 0)), height: num(v("height", 0)), ship_description: String(v("ship_description", "")),
      warranty_months: Math.round(num(v("warranty_months", 0))), active: false, initial_stock: 0 }),
    onSuccess: (p) => { refresh(); toast("Копію створено — вимкнена, доки не перевірите"); onCreated(p.id); },
    onError: (e) => toast(errText(e), "error"),
  });
  useEffect(() => {
    const h = (e: KeyboardEvent) => { if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s" && editable) { e.preventDefault(); if (!save.isPending) saveAll(); } };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  });
  if (!isNew && !data) return <Modal onClose={onClose} size="sm"><Empty><Spinner /></Empty></Modal>;
  const margin = sale - cost;
  const head = (
    <div className="win-head pw-head">
      <IconButton icon={ChevronLeft} label="Назад (Esc)" quiet onClick={onClose} />
      <h2 className="ell">{isNew ? "Новий товар" : String(v("name", ""))}</h2>
      {!isNew && (v("active", true) ? <Tag kind="ok" icon={<BadgeCheck size={12} />}>У продажу</Tag> : <Tag>Не в продажу</Tag>)}
      <div className="acts">
        {editable && !isNew && <Button icon={Copy} disabled={duplicate.isPending} onClick={() => duplicate.mutate()}>Дублювати</Button>}
        {editable && !isNew && <Button variant="danger" icon={data?.sold ? Archive : Trash2} disabled={del.isPending}
          onClick={() => confirmAction(`${data?.sold ? "Перенести в архів" : "Видалити"} «${data?.name}»? Якщо товар уже був у замовленнях, він перейде в архів.`) && del.mutate()}>
          {data?.sold ? "В архів" : "Видалити"}</Button>}
        {editable && <Button variant="primary" icon={Check} kbd="Ctrl S" disabled={save.isPending} onClick={() => saveAll()}>{save.isPending ? "Зберігаю…" : isNew ? "Створити" : "Зберегти"}</Button>}
        <IconButton icon={X} label="Закрити (Esc)" quiet onClick={onClose} />
      </div>
    </div>
  );

  // телефон (мобільна v2): «‹ Товар ⋯», блоки одною колонкою, знизу «Зберегти»
  const mhead = (
    <div className="oc-mhead">
      <RoundButton icon={ChevronLeft} label="Назад" onClick={onClose} />
      <div className="oc-mhead-t"><b>{isNew ? "Новий товар" : "Товар"}</b>{!isNew && <small>{v("active", true) ? "у продажу" : "не в продажу"}</small>}</div>
      {editable && !isNew ? (
        <MenuButton button={({ open, toggle }) => <button type="button" className="rb" aria-label="Ще дії" aria-expanded={open} onClick={toggle}><MoreHorizontal size={20} /></button>}>
          {(close) => (<>
            <button className="pop-item" disabled={duplicate.isPending} onClick={() => { close(); duplicate.mutate(); }}><Copy size={16} />Дублювати</button>
            <button className="pop-item danger" disabled={del.isPending} onClick={() => { close(); if (confirmAction(`${data?.sold ? "Перенести в архів" : "Видалити"} «${data?.name}»?`)) del.mutate(); }}>
              {data?.sold ? <Archive size={16} /> : <Trash2 size={16} />}{data?.sold ? "В архів" : "Видалити"}</button>
          </>)}
        </MenuButton>
      ) : <span className="rb-gap" aria-hidden />}
    </div>
  );
  return (
    <Window size="xl" onClose={onClose} head={mobile ? mhead : head} label={isNew ? "Новий товар" : String(v("name", ""))} bodyClass="pw-body">
      {mobile && editable && (
        <div className="oc-mbar"><Button variant="primary" icon={Check} disabled={save.isPending} onClick={() => saveAll()}>{save.isPending ? "Зберігаю…" : isNew ? "Створити товар" : "Зберегти"}</Button></div>
      )}
      <fieldset className="pw-grid" disabled={!editable}>
        <div className="pw-col">
          <Block title="Основне">
            <MediaTab productId={isNew ? null : (id as number)} photos={data?.photos ?? []} pending={pending} setPending={setPending} compact
              description="" onDescription={() => undefined} onChanged={() => { refresh(); qc.invalidateQueries({ queryKey: ["products", "one", id] }); }} />
            <div className="pw-fields">
              <Field label="Назва"><input value={String(v("name", ""))} onChange={set("name")} required autoFocus={isNew} /></Field>
              <div className="pw-2">
                <Field label="Артикул (SKU)"><input className="mono" value={String(v("sku", ""))} onChange={set("sku")} /></Field>
                <Field label="Категорія"><Select value={String(v("category_id", "") ?? "")} onChange={(e) => setF({ ...f, category_id: e.target.value ? Number(e.target.value) : null })}>
                  <option value="">без категорії</option>{categoryOptions(meta.categories).map((c) => <option key={c.id} value={c.id}>{c.depth ? "· " : ""}{c.label}</option>)}</Select></Field>
                <Field label="Виробник"><Select value={String(v("manufacturer_id", "") ?? "")} onChange={(e) => setF({ ...f, manufacturer_id: e.target.value ? Number(e.target.value) : null })}>
                  <option value="">не вказано</option>{meta.manufacturers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</Select></Field>
                <Field label="Модель"><input value={String(v("model", ""))} onChange={set("model")} placeholder="—" /></Field>
              </div>
              <Field label="Країни продажу" hint="Порожньо — у всіх країнах">
                <MultiSelect placeholder="Усі країни" icon={<Globe size={15} />} value={v<string[]>("countries", [])} onChange={(c) => setF({ ...f, countries: c })}
                  options={Object.entries(meta.countries).map(([c, n]) => ({ value: c, label: n }))} /></Field>
              <label className="check"><input type="checkbox" checked={!!v("active", true)} onChange={set("active")} /> У продажу — показується в замовленнях</label>
            </div>
          </Block>
          <Block title="Опис">
            <textarea className="pw-descr" rows={5} value={String(v("description", ""))} onChange={set("description")} placeholder="Характеристики, комплектація, особливості" aria-label="Опис" />
          </Block>
        </div>
        <div className="pw-col">
          <Block title="Ціни">
            <div className="pw-2">
              <Field label="Ціна продажу, ₴"><input value={String(v("price", ""))} onChange={set("price")} inputMode="decimal" required /></Field>
              <Field label="Акційна ціна, ₴"><input value={num(v("spec_price", 0)) ? String(v("spec_price", "")) : ""} onChange={set("spec_price")} inputMode="decimal" placeholder="—" /></Field>
              <Field label="Оптова ціна, ₴"><input value={num(v("wholesale_price", 0)) ? String(v("wholesale_price", "")) : ""} onChange={set("wholesale_price")} inputMode="decimal" placeholder="—" /></Field>
              <Field label="Собівартість, ₴"><input value={String(v("cost", ""))} onChange={set("cost")} inputMode="decimal" /></Field>
            </div>
            <div className="pw-margin"><Tag kind={margin < 0 ? "bad" : "ok"}>Маржа {money(margin)} ₴{sale ? ` · ${Math.round((margin / sale) * 100)}%` : ""}</Tag>
              <span className="hint">{spec > 0 && price > 0 ? `акція −${Math.max(0, Math.round((1 - spec / price) * 100))}% · ` : ""}рахується сама</span></div>
          </Block>
          <Block title="Склад" acts={!isNew && <button type="button" className="link-btn" onClick={() => setShowMoves((x) => !x)}>Рухи <ChevronRight size={13} className={showMoves ? "rot90" : ""} /></button>}>
            {data && (
              <div className="tiles4 t3">
                <div><b>{data.stock}</b><span>На складі</span></div>
                <div><b>{data.reserved}</b><span>Резерв</span></div>
                <div className={data.available <= data.min_stock ? "warn" : "ok"}><b>{data.available}</b><span>Доступно</span></div>
              </div>
            )}
            <div className="pw-row">
              {isNew && !curVariants.length && <Field label="Початковий залишок, шт"><input type="number" min={0} value={String(f.initial_stock ?? "0")} onChange={set("initial_stock")} /></Field>}
              <Field label="Мінімальний залишок — сповістити"><input type="number" value={String(v("min_stock", "0"))} onChange={set("min_stock")} /></Field>
              {!isNew && <a className="btn" href={`${ROOT}/warehouse?product=${id}`} onClick={(e) => { e.preventDefault(); onClose(); window.history.pushState({}, "", `${ROOT}/warehouse?product=${id}`); window.dispatchEvent(new PopStateEvent("popstate")); }}>
                <Boxes size={15} />Прийняти / списати</a>}
            </div>
            {showMoves && data && <MovesTable moves={data.moves} compact />}
          </Block>
          <Block title="Доставка й гарантія">
            <div className="pw-3">
              <Field label="Вага, кг"><input value={String(v("weight", "0.5"))} onChange={set("weight")} inputMode="decimal" /></Field>
              <Field label="Розміри Д × Ш × В, см"><div className="dims">
                <input value={String(v("length", "") || "")} onChange={set("length")} inputMode="decimal" placeholder="Д" aria-label="Довжина" />
                <input value={String(v("width", "") || "")} onChange={set("width")} inputMode="decimal" placeholder="Ш" aria-label="Ширина" />
                <input value={String(v("height", "") || "")} onChange={set("height")} inputMode="decimal" placeholder="В" aria-label="Висота" /></div></Field>
              <Field label="Гарантія, міс."><input value={String(v("warranty_months", 0))} onChange={set("warranty_months")} inputMode="numeric" /></Field>
            </div>
            <Field label="Опис відправлення для Нової Пошти"><input value={String(v("ship_description", ""))} onChange={set("ship_description")} placeholder="—" /></Field>
          </Block>
        </div>
        <div className="pw-col">
          <Block title="Варіанти" sub={curVariants.length ? `${curVariants.filter((x) => x.active).length} активних` : undefined}>
            <VariantsTab rows={curVariants} onChange={setVariants} isNew={isNew} basePrice={sale} />
          </Block>
          <Block title="Допродаж">
            <Toggle checked={!!v("upsell", false)} onChange={(c) => setF({ ...f, upsell: c })} label="Цей товар — допродаж до інших" />
            {!!v("upsell", false) && (
              <div className="pw-chips">
                <span className="lbl">До яких товарів пропонувати (порожньо — до будь-якого)</span>
                <ChipPicker items={mains} value={curFor} onChange={setUpsellFor} addLabel="Товар" />
              </div>
            )}
            {!isNew && (
              <div className="pw-chips">
                <span className="lbl">Пропонувати разом з цим товаром</span>
                <ChipPicker items={upsellPool} value={offers} onChange={setOfferWith} addLabel="Товар" />
              </div>
            )}
          </Block>
          {!isNew && (
            <section className="summary-block pw-sum">
              <div className="lbl">Продано за 30 днів</div>
              <div className="big">{sold.data ? `${sold.data.qty} шт · ${money(sold.data.sum)} ₴` : "—"}</div>
              {sold.data && (
                <div className="sum-rows">
                  <div><span>Маржа</span><b>{money(sold.data.margin)} ₴</b></div>
                  <div><span>Викуп</span><b>{sold.data.buyout_rate != null ? `${sold.data.buyout_rate}%` : "—"}</b></div>
                  <div><span>З допродажем</span><b>{sold.data.upsell_share != null ? `${sold.data.upsell_share}%` : "—"}</b></div>
                  <div><span>Продано позицій усього</span><b>{sold.data.sold_total}</b></div>
                </div>
              )}
            </section>
          )}
        </div>
      </fieldset>
    </Window>
  );
}

/** Чипи вибраних товарів з × і «+ Товар» (пошук). */
function ChipPicker({ items, value, onChange, addLabel }: { items: Product[]; value: number[]; onChange: (v: number[]) => void; addLabel: string }) {
  const [adding, setAdding] = useState(false);
  const [q, setQ] = useState("");
  const byId = Object.fromEntries(items.map((p) => [p.id, p]));
  const found = items.filter((p) => !value.includes(p.id) && p.name.toLowerCase().includes(q.trim().toLowerCase())).slice(0, 8);
  return (
    <div className="chip-picker">
      {value.map((id) => byId[id] && (
        <span key={id} className="fchip on">{byId[id].name}<span className="x" role="button" tabIndex={0} aria-label={`Прибрати ${byId[id].name}`} onClick={() => onChange(value.filter((x) => x !== id))}><X size={12} /></span></span>
      ))}
      {adding ? (
        <span className="chip-sel">
          <input className="chip-add-in" autoFocus value={q} onChange={(e) => setQ(e.target.value)} placeholder="Назва товару" onBlur={() => setTimeout(() => { setAdding(false); setQ(""); }, 150)}
            onKeyDown={(e) => { if (e.key === "Enter" && found[0]) { e.preventDefault(); onChange([...value, found[0].id]); setQ(""); } if (e.key === "Escape") { e.stopPropagation(); setAdding(false); } }} />
          {found.length > 0 && <div className="pop chip-pop">{found.map((p) => <button key={p.id} type="button" className="pop-item" onMouseDown={(e) => { e.preventDefault(); onChange([...value, p.id]); setQ(""); }}>{p.name}</button>)}</div>}
        </span>
      ) : <button type="button" className="fchip" onClick={() => setAdding(true)}><Plus size={13} />{addLabel}</button>}
    </div>
  );
}

function MediaTab({ productId, photos, pending, setPending, description, onDescription, onChanged, compact }: {
  productId: number | null; photos: { id: number; url: string }[]; pending: File[]; setPending: (f: File[]) => void;
  description: string; onDescription: (d: string) => void; onChanged: () => void; compact?: boolean;
}) {
  const toast = useToast();
  const input = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [order, setOrder] = useState<number[] | null>(null);
  const shown = order ? order.map((x) => photos.find((p) => p.id === x)).filter(Boolean) as typeof photos : photos;
  const dragId = useRef<number | null>(null);
  const previews = useMemo(() => pending.map((f) => URL.createObjectURL(f)), [pending]);
  useEffect(() => () => previews.forEach((u) => URL.revokeObjectURL(u)), [previews]);
  const add = (files: FileList | null) => {
    if (!files) return;
    const ok = [...files].filter((f) => /image\/(jpeg|png|webp|gif)/.test(f.type));
    if (ok.length < files.length) toast("Підтримуються JPG, PNG, WEBP і GIF", "warn");
    setPending([...pending, ...ok]);
  };
  const remove = async (pid: number) => {
    if (!productId) return;
    try { await api.del(`/products/${productId}/photos/${pid}`); onChanged(); } catch (e) { toast(errText(e), "error"); }
  };
  const reorder = async (ids: number[]) => {
    setOrder(ids);
    if (productId) { try { await api.put(`/products/${productId}/photos`, ids); onChanged(); } catch (e) { toast(errText(e), "error"); } }
  };
  return (
    <>
      <div className={`pm-drop ${drag ? "on" : ""}${compact ? " compact" : ""}`} onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); add(e.dataTransfer.files); }}>
        <div className="pm-photos">
          {shown.map((p, i) => (
            <div key={p.id} className="pm-photo" draggable onDragStart={() => { dragId.current = p.id; }}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); e.stopPropagation(); const from = dragId.current; if (from == null || from === p.id) return;
                const ids = shown.map((x) => x.id).filter((x) => x !== from); ids.splice(ids.indexOf(p.id), 0, from); reorder(ids); }}>
              <img src={`${ROOT}${p.url}`} alt="" />{i === 0 && <span className="main-tag">головне</span>}
              <span className="grip"><GripVertical size={14} /></span>
              <button type="button" className="rm" title="Видалити фото" onClick={() => remove(p.id)}><X size={14} /></button>
            </div>
          ))}
          {previews.map((u, i) => (
            <div key={u} className="pm-photo pending"><img src={u} alt="" /><span className="main-tag">збережеться</span>
              <button type="button" className="rm" title="Прибрати" onClick={() => setPending(pending.filter((_, j) => j !== i))}><X size={14} /></button></div>
          ))}
          <button type="button" className="pm-add" title="Додати фото (або перетягніть сюди)" onClick={() => input.current?.click()}><ImagePlus size={22} />{!compact && <><span>Додати фото</span><small>або перетягніть сюди</small></>}</button>
        </div>
        <input ref={input} type="file" accept="image/jpeg,image/png,image/webp,image/gif" multiple hidden onChange={(e) => { add(e.target.files); e.target.value = ""; }} />
      </div>
      {!compact && <p className="hint">Перше фото — головне: його видно в списку товарів і в замовленні. Порядок змінюється перетягуванням. До 20 фото, до 10 МБ кожне.</p>}
      {!compact && <Field label="Опис"><textarea rows={8} value={description} onChange={(e) => onDescription(e.target.value)} placeholder="Характеристики, комплектація, особливості" /></Field>}
    </>
  );
}

function VariantsTab({ rows, onChange, isNew, basePrice }: { rows: VRow[]; onChange: (r: VRow[]) => void; isNew: boolean; basePrice: number }) {
  const { data: groups } = useQuery({ queryKey: ["attributes"], queryFn: () => api.get<AttributeGroup[]>("/catalog/attributes") });
  const [picked, setPicked] = useState<Record<number, number[]>>({});
  const names = useMemo(() => Object.fromEntries((groups ?? []).flatMap((g) => g.attributes.map((a) => [a.id, a.name]))), [groups]);
  const generate = () => {
    const sets = (groups ?? []).map((g) => picked[g.id] ?? []).filter((x) => x.length);
    if (!sets.length) return;
    const combos = sets.reduce<number[][]>((acc, s) => acc.flatMap((c) => s.map((x) => [...c, x])), [[]]);
    const have = new Set(rows.map((r) => [...r.attribute_ids].sort().join(",")));
    const fresh = combos.filter((c) => !have.has([...c].sort().join(","))).map((c) => ({ name: c.map((x) => names[x]).join(" / "), sku: "", attribute_ids: c, price: "", active: true, initial_stock: "" }));
    onChange([...rows, ...fresh]);
    setPicked({});
  };
  const upd = (i: number, patch: Partial<VRow>) => onChange(rows.map((r, j) => (j === i ? { ...r, ...patch } : r)));
  return (
    <>
      <p className="hint">Варіанти — поєднання атрибутів (колір, розмір…). У кожного свій залишок; ціна й артикул — за потреби, інакше як у товару.</p>
      {groups && groups.length > 0 ? (
        <div className="vg">
          {groups.map((g) => (
            <div key={g.id} className="vg-row"><span className="vg-name">{g.name}</span>
              <div className="chips">{g.attributes.filter((a) => a.active).map((a) => {
                const on = (picked[g.id] ?? []).includes(a.id);
                return <button type="button" key={a.id} className={`chip ${on ? "on" : ""}`} onClick={() => setPicked({ ...picked, [g.id]: on ? (picked[g.id] ?? []).filter((x) => x !== a.id) : [...(picked[g.id] ?? []), a.id] })}>{a.name}</button>;
              })}</div></div>
          ))}
          <button type="button" className="btn sm" disabled={!Object.values(picked).some((x) => x.length)} onClick={generate}><Wand2 size={14} /> Додати поєднання</button>
        </div>
      ) : groups && <p className="hint">Атрибути ще не заведено — «Товари» → «Атрибути». Або додайте варіант вручну.</p>}
      {rows.length > 0 && (
        <table className="t dense vt">
          <thead><tr><th>Варіант</th><th>Артикул</th><th className="num">Ціна, ₴</th><th className="num">{isNew ? "Залишок" : "На складі"}</th><th>Активний</th><th /></tr></thead>
          <tbody>{rows.map((r, i) => (
            <tr key={r.id ?? `n${i}`} className={r.active ? "" : "off"}>
              <td><input value={r.name} onChange={(e) => upd(i, { name: e.target.value })} placeholder="Назва варіанта" /></td>
              <td><input className="mono" value={r.sku} onChange={(e) => upd(i, { sku: e.target.value })} placeholder="—" /></td>
              <td className="num"><input value={r.price} onChange={(e) => upd(i, { price: e.target.value })} placeholder={money(basePrice)} inputMode="decimal" /></td>
              <td className="num">{r.id ? <b>{r.stock ?? 0}</b> : <input type="number" min={0} value={r.initial_stock} onChange={(e) => upd(i, { initial_stock: e.target.value })} placeholder="0" />}</td>
              <td><input type="checkbox" checked={r.active} onChange={(e) => upd(i, { active: e.target.checked })} /></td>
              <td><button type="button" className="btn icon ghost" title="Прибрати варіант" onClick={() => onChange(rows.filter((_, j) => j !== i))}><Trash2 size={14} /></button></td>
            </tr>
          ))}</tbody>
        </table>
      )}
      <button type="button" className="btn sm" onClick={() => onChange([...rows, { name: "", sku: "", attribute_ids: [], price: "", active: true, initial_stock: "" }])}><Plus size={14} /> Варіант вручну</button>
      {rows.some((r) => r.id && !r.active) && <p className="hint">Варіант, який уже продавався, не видаляється, а вимикається — щоб не зламати історію замовлень.</p>}
    </>
  );
}

// ---------------------------------------------------------------- довідники каталогу
function useDir<T>(key: string, path: string) {
  const qc = useQueryClient();
  const toast = useToast();
  const q = useQuery({ queryKey: [key], queryFn: () => api.get<T[]>(path) });
  const mut = useMutation({
    mutationFn: ({ method, url, body }: { method: "post" | "del"; url: string; body?: Record<string, unknown> }) =>
      method === "del" ? api.del<T[]>(url) : api.post<T[]>(url, body),
    onSuccess: (rows) => { qc.setQueryData([key], rows); qc.invalidateQueries({ queryKey: ["meta"] }); qc.invalidateQueries({ queryKey: ["products"] }); },
    onError: (e) => toast(errText(e), "error"),
  });
  return { data: q.data, mut };
}

function InlineName({ value, onSave, placeholder }: { value: string; onSave: (v: string) => void; placeholder?: string }) {
  const [v, setV] = useState(value);
  useEffect(() => setV(value), [value]);
  return <input className="inline-name" value={v} placeholder={placeholder} onChange={(e) => setV(e.target.value)}
    onBlur={() => { if (v.trim() && v !== value) onSave(v.trim()); else setV(value); }}
    onKeyDown={(e) => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); if (e.key === "Escape") { setV(value); (e.target as HTMLInputElement).blur(); } }} />;
}

function AddRow({ placeholder, onAdd, children }: { placeholder: string; onAdd: (name: string) => void; children?: React.ReactNode }) {
  const [v, setV] = useState("");
  return (
    <form className="dir-add" onSubmit={(e) => { e.preventDefault(); if (v.trim()) { onAdd(v.trim()); setV(""); } }}>
      <input value={v} onChange={(e) => setV(e.target.value)} placeholder={placeholder} />{children}
      <button className="btn" disabled={!v.trim()}><Plus size={14} /> Додати</button>
    </form>
  );
}

function CategoriesTab() {
  const { data, mut } = useDir<Category>("categories", "/catalog/categories");
  const [parent, setParent] = useState("");
  if (!data) return <Empty><Spinner /></Empty>;
  const roots = data.filter((c) => !c.parent_id);
  const save = (c: Partial<Category> & { name: string }) => mut.mutate({ method: "post", url: "/catalog/categories", body: { id: c.id, name: c.name, parent_id: c.parent_id ?? null, active: c.active ?? true } });
  const row = (c: Category, depth: number) => (
    <div key={c.id} className={`dir-row ${depth ? "sub" : ""} ${c.active ? "" : "off"}`}>
      <FolderTree size={15} className="muted" />
      <InlineName value={c.name} onSave={(name) => save({ ...c, name })} />
      <span className="muted dir-n">{c.products} тов.</span>
      <label className="check" title="Показувати в списках"><input type="checkbox" checked={c.active} onChange={(e) => save({ ...c, active: e.target.checked })} /></label>
      <button className="btn icon ghost" title="Видалити (товари залишаться без категорії)" onClick={() => confirmAction(`Видалити категорію «${c.name}»? Товари залишаться без категорії.`) && mut.mutate({ method: "del", url: `/catalog/categories/${c.id}` })}><Trash2 size={14} /></button>
    </div>
  );
  return (
    <div className="card dir">
      <AddRow placeholder="Нова категорія" onAdd={(name) => save({ name, parent_id: parent ? Number(parent) : null })}>
        <Select value={parent} onChange={(e) => setParent(e.target.value)} style={{ width: "auto" }}><option value="">розділ (верхній рівень)</option>{roots.map((r) => <option key={r.id} value={r.id}>у «{r.name}»</option>)}</Select>
      </AddRow>
      {roots.map((r) => <div key={r.id}>{row(r, 0)}{data.filter((c) => c.parent_id === r.id).map((c) => row(c, 1))}</div>)}
      {!data.length && <Empty><FolderTree size={22} className="e-ico" />Категорій ще немає. Почніть із розділів, наприклад «Мікрофони» чи «Світло».</Empty>}
    </div>
  );
}

function ManufacturersTab() {
  const { data, mut } = useDir<Manufacturer>("manufacturers", "/catalog/manufacturers");
  if (!data) return <Empty><Spinner /></Empty>;
  const save = (m: Partial<Manufacturer> & { name: string }) => mut.mutate({ method: "post", url: "/catalog/manufacturers", body: { id: m.id, name: m.name, active: m.active ?? true } });
  return (
    <div className="card dir">
      <AddRow placeholder="Новий виробник, наприклад DJI" onAdd={(name) => save({ name })} />
      {data.map((m) => (
        <div key={m.id} className={`dir-row ${m.active ? "" : "off"}`}>
          <Factory size={15} className="muted" /><InlineName value={m.name} onSave={(name) => save({ ...m, name })} />
          <span className="muted dir-n">{m.products} тов.</span>
          <button className="btn icon ghost" title="Видалити" onClick={() => confirmAction(`Видалити виробника «${m.name}»?`) && mut.mutate({ method: "del", url: `/catalog/manufacturers/${m.id}` })}><Trash2 size={14} /></button>
        </div>
      ))}
      {!data.length && <Empty><Factory size={22} className="e-ico" />Виробників ще немає.</Empty>}
    </div>
  );
}

function AttributesTab() {
  const { data, mut } = useDir<AttributeGroup>("attributes", "/catalog/attributes");
  if (!data) return <Empty><Spinner /></Empty>;
  return (
    <div className="stack">
      <div className="card dir"><AddRow placeholder="Нова категорія атрибутів: Колір, Розмір, Пам'ять…" onAdd={(name) => mut.mutate({ method: "post", url: "/catalog/attribute-groups", body: { name } })} /></div>
      {data.map((g) => (
        <div key={g.id} className="card dir">
          <div className="dir-row head-row"><Tags size={15} className="muted" />
            <InlineName value={g.name} onSave={(name) => mut.mutate({ method: "post", url: "/catalog/attribute-groups", body: { id: g.id, name } })} />
            <button className="btn icon ghost" title="Видалити категорію атрибутів" onClick={() => confirmAction(`Видалити «${g.name}» з усіма значеннями?`) && mut.mutate({ method: "del", url: `/catalog/attribute-groups/${g.id}` })}><Trash2 size={14} /></button>
          </div>
          <div className="attr-chips">
            {g.attributes.map((a) => (
              <span key={a.id} className={`attr-chip ${a.active ? "" : "off"}`} title={a.active ? "" : "Вимкнено: уже є у варіантах товарів"}>{a.name}
                <button title="Видалити" onClick={() => mut.mutate({ method: "del", url: `/catalog/attributes/${a.id}` })}><X size={12} /></button></span>
            ))}
            <AddRow placeholder={`Нове значення для «${g.name}»`} onAdd={(name) => mut.mutate({ method: "post", url: "/catalog/attributes", body: { group_id: g.id, name } })} />
          </div>
        </div>
      ))}
    </div>
  );
}
