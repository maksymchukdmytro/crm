// Товари: список з фото й фільтрами; картка товару з вкладками (основне, фото й опис, варіанти, доставка, склад);
// довідники каталогу — категорії (два рівні), виробники, атрибути для варіантів.
import { useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Archive, Boxes, Factory, FolderTree, Globe, GripVertical, ImagePlus, Layers, Package, Plus, Tags, Trash2, Truck, Wand2, X,
} from "lucide-react";
import { api, qs, ROOT } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { money, num } from "../lib/format";
import type { AttributeGroup, Category, Manufacturer, Product, ProductDetail } from "../lib/types";
import { Badge, confirmAction, Empty, Field, Kpi, Modal, Spinner } from "../components/ui";
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
  useEffect(() => { if (sp.get("new")) { setEdit("new"); const n = new URLSearchParams(sp); n.delete("new"); setSp(n, { replace: true }); } }, [sp, setSp]);
  const dq = useDebounced(q, 250);
  const params = { q: dq, show, category, manufacturer, stock_state: stockState };
  const { data, isLoading } = useQuery({ queryKey: ["products", params], queryFn: () => api.get<Product[]>(`/products${qs(params)}`) });
  const cats = useMemo(() => Object.fromEntries(meta.categories.map((c) => [c.id, c.name])), [meta.categories]);
  const brands = useMemo(() => Object.fromEntries(meta.manufacturers.map((m) => [m.id, m.name])), [meta.manufacturers]);
  const catOpts = categoryOptions(meta.categories);

  return (
    <>
      <div className="filters">
        <input type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Назва, артикул або модель" />
        {catOpts.length > 0 && <select value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="">Усі категорії</option><option value="-1">Без категорії</option>
          {catOpts.map((c) => <option key={c.id} value={c.id}>{c.depth ? "  · " : ""}{c.label}</option>)}</select>}
        {meta.manufacturers.length > 0 && <select value={manufacturer} onChange={(e) => setManufacturer(e.target.value)}>
          <option value="">Усі виробники</option>{meta.manufacturers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select>}
        <select value={stockState} onChange={(e) => setStockState(e.target.value)}>
          <option value="">Будь-який залишок</option><option value="in">Є в наявності</option><option value="low">Закінчується</option>
          <option value="out">Немає</option><option value="minus">Мінус</option></select>
        <select value={show} onChange={(e) => setShow(e.target.value)}><option value="active">Активні</option><option value="inactive">Архів</option><option value="all">Усі</option></select>
        <span className="spacer" />
        {editable && <button className="btn primary" onClick={() => setEdit("new")}><Plus size={15} /> Товар</button>}
      </div>
      <div className="card flush tablewrap">
        <table className="t pr-table">
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
      </div>
      {edit !== null && <ProductModal id={edit} editable={editable} onClose={() => setEdit(null)} onCreated={(id) => setEdit(id)} />}
    </>
  );
}

// ---------------------------------------------------------------- картка товару
type VRow = { id?: number; name: string; sku: string; attribute_ids: number[]; price: string; active: boolean; initial_stock: string; stock?: number; reserved?: number };

function ProductModal({ id, editable, onClose, onCreated }: { id: number | "new"; editable: boolean; onClose: () => void; onCreated: (id: number) => void }) {
  const isNew = id === "new";
  const qc = useQueryClient();
  const toast = useToast();
  const meta = useMeta();
  const { data } = useQuery({ queryKey: ["products", "one", id], queryFn: () => api.get<ProductDetail>(`/products/${id}`), enabled: !isNew });
  const [tab, setTab] = useState("main");
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
  if (!isNew && !data) return <Modal onClose={onClose} size="sm"><Empty><Spinner /></Empty></Modal>;
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
    setF({ ...f, [k]: e.target instanceof HTMLInputElement && e.target.type === "checkbox" ? e.target.checked : e.target.value });
  const price = num(v("price", 0)), spec = num(v("spec_price", 0)), cost = num(v("cost", 0));
  const sale = spec > 0 ? spec : price;
  const tabs: [string, string, typeof Package, number?][] = [["main", "Основне", Package], ["media", "Фото й опис", ImagePlus, (data?.photos?.length ?? 0) + pending.length],
    ["variants", "Варіанти", Layers, curVariants.filter((x) => x.active).length], ["shipping", "Доставка", Truck], ...(data ? [["stock", "Склад", Boxes] as [string, string, typeof Package]] : [])];

  return (
    <Modal onClose={onClose} size="lg" title={<>{data?.photo && <img className="pm-title-ph" src={`${ROOT}${data.photo}`} alt="" />}{isNew ? "Новий товар" : String(v("name", ""))}</>}>
      <nav className="subnav pm-tabs">{tabs.map(([k, label, Icon, n]) => <a key={k} className={tab === k ? "on" : ""} onClick={() => setTab(k)}><Icon size={14} /> {label}{n ? <span className="n">{n}</span> : null}</a>)}</nav>
      <form className="form pm-form" onSubmit={(e) => { e.preventDefault(); save.mutate(); }}>
        <fieldset disabled={!editable}>
          {tab === "main" && <>
            <Field label="Назва"><input value={String(v("name", ""))} onChange={set("name")} required autoFocus={isNew} /></Field>
            <div className="cols c3">
              <Field label="Категорія"><select value={String(v("category_id", "") ?? "")} onChange={(e) => setF({ ...f, category_id: e.target.value ? Number(e.target.value) : null })}>
                <option value="">без категорії</option>{categoryOptions(meta.categories).map((c) => <option key={c.id} value={c.id}>{c.depth ? "· " : ""}{c.label}</option>)}</select></Field>
              <Field label="Виробник"><select value={String(v("manufacturer_id", "") ?? "")} onChange={(e) => setF({ ...f, manufacturer_id: e.target.value ? Number(e.target.value) : null })}>
                <option value="">не вказано</option>{meta.manufacturers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}</select></Field>
              <Field label="Модель"><input value={String(v("model", ""))} onChange={set("model")} placeholder="VL49 RGB" /></Field>
            </div>
            <div className="cols c3">
              <Field label="Артикул (SKU)" hint="Для заявок з лендингу й маркетплейсів"><input className="mono" value={String(v("sku", ""))} onChange={set("sku")} /></Field>
              <Field label="Ціна продажу, ₴"><input value={String(v("price", ""))} onChange={set("price")} inputMode="decimal" required /></Field>
              <Field label="Акційна ціна, ₴" hint={spec > 0 && price > 0 ? `Знижка ${Math.max(0, Math.round((1 - spec / price) * 100))}% — у замовленні буде акційна` : "Порожньо — без акції"}>
                <input value={num(v("spec_price", 0)) ? String(v("spec_price", "")) : ""} onChange={set("spec_price")} inputMode="decimal" placeholder="—" /></Field>
              <Field label="Собівартість, ₴" hint="Середня, оновлюється при оприбуткуванні"><input value={String(v("cost", ""))} onChange={set("cost")} inputMode="decimal" /></Field>
              <Field label="Оптова ціна, ₴"><input value={num(v("wholesale_price", 0)) ? String(v("wholesale_price", "")) : ""} onChange={set("wholesale_price")} inputMode="decimal" placeholder="—" /></Field>
              <Field label="Маржа"><div className={`pm-margin ${sale - cost < 0 ? "neg" : ""}`}>{money(sale - cost)} ₴ <small>{sale ? `${Math.round(((sale - cost) / sale) * 100)}%` : ""}</small></div></Field>
            </div>
            <div className="cols">
              {isNew && !curVariants.length && <Field label="Початковий залишок, шт"><input type="number" min={0} value={String(f.initial_stock ?? "0")} onChange={set("initial_stock")} /></Field>}
              <Field label="Мінімальний залишок" hint="Нижче — підсвічується в списку"><input type="number" value={String(v("min_stock", "0"))} onChange={set("min_stock")} /></Field>
              <Field label="Країни продажу" hint="Порожньо — товар продається в усіх країнах">
                <MultiSelect placeholder="Усі країни" icon={<Globe size={15} />} value={v<string[]>("countries", [])} onChange={(c) => setF({ ...f, countries: c })}
                  options={Object.entries(meta.countries).map(([c, n]) => ({ value: c, label: n }))} /></Field>
            </div>
            <div className="checks">
              <label className="check"><input type="checkbox" checked={!!v("upsell", false)} onChange={set("upsell")} /> Допродаж — пропонувати менеджеру до інших товарів</label>
              {!!v("upsell", false) && (
                <div className="upsell-box">
                  <span className="lbl">До яких товарів пропонувати</span>
                  {mains.length ? <div className="chips">{mains.map((p) => {
                    const on = curFor.includes(p.id);
                    return <button type="button" key={p.id} className={`chip ${on ? "on" : ""}`} onClick={() => setUpsellFor(on ? curFor.filter((x) => x !== p.id) : [...curFor, p.id])}>{p.name}</button>;
                  })}</div> : <span className="hint">Спершу додайте основні товари.</span>}
                </div>
              )}
              <label className="check"><input type="checkbox" checked={!!v("active", true)} onChange={set("active")} /> Активний — показується в замовленнях</label>
            </div>
          </>}
          {tab === "media" && <MediaTab productId={isNew ? null : (id as number)} photos={data?.photos ?? []} pending={pending} setPending={setPending}
            description={String(v("description", ""))} onDescription={(d) => setF({ ...f, description: d })} onChanged={() => { refresh(); qc.invalidateQueries({ queryKey: ["products", "one", id] }); }} />}
          {tab === "variants" && <VariantsTab rows={curVariants} onChange={setVariants} isNew={isNew} basePrice={sale} />}
          {tab === "shipping" && <>
            <Field label="Опис відправлення для Нової Пошти" hint="Наприклад «Аксесуари до фототехніки». Підставляється в ТТН разом із розмірами"><input value={String(v("ship_description", ""))} onChange={set("ship_description")} /></Field>
            <Field label="Гарантія, міс." hint="Для гарантійного талону; 0 — як у налаштуваннях документів"><input value={String(v("warranty_months", 0))} onChange={set("warranty_months")} inputMode="numeric" /></Field>
            <div className="cols c3">
              <Field label="Вага, кг"><input value={String(v("weight", "0.5"))} onChange={set("weight")} inputMode="decimal" /></Field>
              <Field label="Довжина, см"><input value={String(v("length", "") || "")} onChange={set("length")} inputMode="decimal" placeholder="—" /></Field>
              <Field label="Ширина, см"><input value={String(v("width", "") || "")} onChange={set("width")} inputMode="decimal" placeholder="—" /></Field>
              <Field label="Висота, см"><input value={String(v("height", "") || "")} onChange={set("height")} inputMode="decimal" placeholder="—" /></Field>
            </div>
          </>}
          {tab === "stock" && data && <div className="stack">
            <div className="kpis" style={{ margin: 0 }}>
              <Kpi label="На складі" value={data.stock} /><Kpi label="Резерв" value={data.reserved} />
              <Kpi label="Доступно" value={<span className={data.available <= data.min_stock ? "lowstock" : ""}>{data.available}</span>} />
              <Kpi label="Продано позицій" value={data.sold} />
            </div>
            {(data.variants ?? []).length > 0 && <table className="t dense"><thead><tr><th>Варіант</th><th className="num">На складі</th><th className="num">Резерв</th><th className="num">Доступно</th></tr></thead>
              <tbody>{(data.variants ?? []).map((x) => <tr key={x.id} className={x.active ? "" : "muted"}><td>{x.name}{!x.active && " (вимкнено)"}</td><td className="num">{x.stock}</td><td className="num">{x.reserved}</td><td className="num"><b>{x.available}</b></td></tr>)}</tbody></table>}
            <p className="hint">Змінити залишок — розділ «Склад» → «Коригування».</p>
            <MovesTable moves={data.moves} compact />
          </div>}
        </fieldset>
        {editable && <div className="pm-bar">
          {!isNew && <button type="button" className="btn danger" disabled={del.isPending}
            onClick={() => confirmAction(`Видалити «${data?.name}»? Якщо товар уже був у замовленнях, він перейде в архів.`) && del.mutate()}>
            {data?.sold ? <><Archive size={15} /> В архів</> : <><Trash2 size={15} /> Видалити</>}</button>}
          <span className="spacer" />
          <button type="button" className="btn" onClick={onClose}>Скасувати</button>
          <button className="btn primary" disabled={save.isPending}>{save.isPending ? "Збереження…" : isNew ? "Створити товар" : "Зберегти"}</button>
        </div>}
      </form>
    </Modal>
  );
}

function MediaTab({ productId, photos, pending, setPending, description, onDescription, onChanged }: {
  productId: number | null; photos: { id: number; url: string }[]; pending: File[]; setPending: (f: File[]) => void;
  description: string; onDescription: (d: string) => void; onChanged: () => void;
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
      <div className={`pm-drop ${drag ? "on" : ""}`} onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
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
          <button type="button" className="pm-add" onClick={() => input.current?.click()}><ImagePlus size={22} /><span>Додати фото</span><small>або перетягніть сюди</small></button>
        </div>
        <input ref={input} type="file" accept="image/jpeg,image/png,image/webp,image/gif" multiple hidden onChange={(e) => { add(e.target.files); e.target.value = ""; }} />
      </div>
      <p className="hint">Перше фото — головне: його видно в списку товарів і в замовленні. Порядок змінюється перетягуванням. До 20 фото, до 10 МБ кожне.</p>
      <Field label="Опис"><textarea rows={8} value={description} onChange={(e) => onDescription(e.target.value)} placeholder="Характеристики, комплектація, особливості" /></Field>
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
        <select value={parent} onChange={(e) => setParent(e.target.value)} style={{ width: "auto" }}><option value="">розділ (верхній рівень)</option>{roots.map((r) => <option key={r.id} value={r.id}>у «{r.name}»</option>)}</select>
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
