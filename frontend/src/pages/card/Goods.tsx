// «Товари — компактні» (UI-DESIGN §5.4, макет 01): рядок 46 px — фото 34 · назва · варіант-пігулка · артикул і залишок · − 1 + · сума · ×;
// допродаж — з відступом під своїм товаром (40 px); пошук «Додати товар»; пунктирна плашка «Часто беруть разом».
import { forwardRef, useImperativeHandle, useMemo, useRef, useState } from "react";
import { ChevronDown, Link2, Package, Plus, Search, Sparkles, X } from "lucide-react";
import { ROOT } from "../../lib/api";
import { money, num } from "../../lib/format";
import type { OrderItem, Product, Variant } from "../../lib/types";
import { QtyStepper } from "../../components/ui";
import { arrange, newKey } from "./state";

type Pick = { p: Product; v?: Variant };
export type GoodsHandle = { focusSearch: () => void; startUpsell: () => void };

export const Goods = forwardRef<GoodsHandle, {
  items: OrderItem[]; products: Product[]; onChange: (i: OrderItem[]) => void; readOnly?: boolean; autoFocusSearch?: boolean;
}>(function Goods({ items: raw, products, onChange: emit, readOnly, autoFocusSearch }, ref) {
  const items = useMemo(() => arrange(raw), [raw]);
  const onChange = (next: OrderItem[]) => emit(arrange(next));
  const [upFor, setUpFor] = useState<string | null>(null);
  const search = useRef<HTMLInputElement>(null);
  const byId = useMemo(() => Object.fromEntries(products.map((p) => [p.id, p])), [products]);
  const mains = items.filter((i) => !i.upsell);
  const mainProducts = mains.filter((i) => i.product_id);
  const inOrder = new Set(items.map((i) => i.product_id).filter(Boolean) as number[]);
  useImperativeHandle(ref, () => ({
    focusSearch: () => search.current?.focus(),
    startUpsell: () => { const m = mainProducts[0]; if (m) setUpFor(m.key ?? null); else search.current?.focus(); },
  }));

  // «Часто беруть разом» — лише коли в замовленні вже є основний товар; кожна пропозиція додається окремо своєю кнопкою
  const offers = mainProducts.length ? products.filter((p) => p.upsell && p.active !== false && !inOrder.has(p.id) && (
    !p.upsell_for?.length || p.upsell_for.some((id) => inOrder.has(id)))).slice(0, 3) : [];

  const line = (x: Pick, upsell: boolean, mainPid: number | null): OrderItem => {
    const { p, v } = x;
    const price = v?.price ?? p.sale_price ?? p.price;
    return { product_id: p.id, variant_id: v?.id ?? null, variant_name: v?.name ?? "", name: v ? `${p.name} (${v.name})` : p.name,
      price: String(price), qty: 1, upsell, upsell_for: upsell ? mainPid : null, base_price: price, photo: p.photo,
      sku: v?.sku || p.sku, available: (v ?? p).available, key: newKey() };
  };
  const addMain = (x?: Pick, text = "") => {
    if (!x) { if (text) onChange([...items, { product_id: null, name: text, price: "", qty: 1, upsell: false, upsell_for: null, key: newKey() }]); return; }
    const ex = items.find((i) => i.product_id === x.p.id && (i.variant_id ?? null) === (x.v?.id ?? null));
    if (ex) { onChange(items.map((i) => (i === ex ? { ...i, qty: i.qty + 1 } : i))); return; }
    const main = x.p.upsell ? mainProducts.find((m) => x.p.upsell_for?.includes(m.product_id!)) ?? (x.p.upsell_for?.length ? undefined : mainProducts[0]) : undefined;
    onChange([...items, line(x, !!main, main?.product_id ?? null)]);
  };
  const addUpsell = (m: OrderItem | undefined, x: Pick) => {
    const ex = items.find((i) => i.product_id === x.p.id && (i.variant_id ?? null) === (x.v?.id ?? null));
    if (ex) onChange(items.map((i) => (i === ex ? { ...i, qty: i.qty + 1, upsell: true, upsell_for: m?.product_id ?? null } : i)));
    else onChange([...items, line(x, true, m?.product_id ?? null)]);
    setUpFor(null);
  };
  const upd = (key: string | undefined, patch: Partial<OrderItem>) => onChange(items.map((i) => (i.key === key ? { ...i, ...patch } : i)));
  const remove = (it: OrderItem) => onChange(items.filter((x) => x.key !== it.key).map((x) =>
    x.upsell && it.product_id && !it.upsell && x.upsell_for === it.product_id && !items.some((o) => o !== it && !o.upsell && o.product_id === it.product_id) ? { ...x, upsell_for: null } : x));

  const row = (i: OrderItem) => {
    const p = i.product_id ? byId[i.product_id] : undefined;
    const base = i.base_price ?? p?.price;
    const changed = base != null && i.price !== "" && num(i.price) !== Number(base);
    const variants = (p?.variants ?? []).filter((x) => x.active || x.id === i.variant_id);
    const avail = i.variant_id ? variants.find((x) => x.id === i.variant_id)?.available : p?.available ?? i.available;
    const sku = i.variant_id ? variants.find((x) => x.id === i.variant_id)?.sku || p?.sku : p?.sku ?? i.sku;
    const photo = i.photo ?? p?.photo;
    const baseName = p && i.variant_id ? p.name : i.name;
    return (
      <div key={i.key} className={`gi${i.upsell ? " up" : ""}`}>
        <span className="gi-ph">{i.upsell ? <Link2 size={15} /> : photo ? <img src={`${ROOT}${photo}`} alt="" /> : <Package size={15} />}</span>
        <div className="gi-main">
          <div className="gi-l1">
            {p ? <span className="gi-name ell" title={i.name}>{baseName}</span>
              : <input className="gi-name-in" value={i.name} disabled={readOnly} onChange={(e) => upd(i.key, { name: e.target.value })} placeholder="Назва позиції" aria-label="Назва позиції" />}
            {variants.length > 0 && (
              <label className="gi-var" title="Варіант">
                <span className="ell">{variants.find((x) => x.id === i.variant_id)?.name ?? "варіант"}</span><ChevronDown size={12} />
                <select value={i.variant_id ?? ""} disabled={readOnly} aria-label="Варіант"
                  onChange={(e) => { const nv = variants.find((x) => x.id === Number(e.target.value)); upd(i.key, { variant_id: nv?.id ?? null, variant_name: nv?.name ?? "", name: nv ? `${p!.name} (${nv.name})` : p!.name, price: String(nv?.price ?? p!.sale_price ?? p!.price), base_price: nv?.price ?? p!.sale_price ?? p!.price }); }}>
                  <option value="">варіант…</option>
                  {variants.map((x) => <option key={x.id} value={x.id}>{x.name} · {x.available} шт</option>)}
                </select>
              </label>
            )}
            <span className="gi-meta">
              {i.upsell && <span>допродаж</span>}
              {sku && <span className="mono">{sku}</span>}
              {avail != null && p && <span className={avail < i.qty ? "t-bad" : ""}>{avail} шт</span>}
            </span>
          </div>
          {!readOnly && (
            <div className="gi-l2">
              {i.upsell
                ? <button type="button" className="gi-link" onClick={() => upd(i.key, { upsell: false, upsell_for: null })}>зробити основним</button>
                : i.product_id && <button type="button" className="gi-link" onClick={() => setUpFor(upFor === i.key ? null : i.key ?? null)}><Plus size={11} />Допродаж</button>}
              {i.upsell && mainProducts.length > 1 && (
                <select className="gi-mini" value={i.upsell_for ?? ""} aria-label="До якого товару" onChange={(e) => upd(i.key, { upsell_for: e.target.value ? Number(e.target.value) : null })}>
                  <option value="">до замовлення</option>{mainProducts.map((m) => <option key={m.key} value={m.product_id!}>до «{m.name}»</option>)}
                </select>
              )}
              {changed && <span className="gi-was">ціна в каталозі {money(base!)} ₴</span>}
            </div>
          )}
        </div>
        {readOnly ? <span className="gi-qty-ro">{i.qty} шт</span> : <QtyStepper value={i.qty} onChange={(q) => upd(i.key, { qty: q })} />}
        <label className={`gi-price${i.qty > 1 ? " show" : ""}`} title="Ціна за одиницю — можна змінити лише для цього замовлення">
          <input value={i.price} inputMode="decimal" disabled={readOnly} aria-label="Ціна за одиницю" onChange={(e) => upd(i.key, { price: e.target.value.replace(",", ".") })} />
          <span className="gi-sum num">{money(num(i.price) * i.qty)} ₴</span>
        </label>
        {!readOnly && <button type="button" className="gi-x" aria-label="Прибрати позицію" title="Прибрати" onClick={() => remove(i)}><X size={14} /></button>}
      </div>
    );
  };

  const body: React.ReactNode[] = [];
  items.forEach((i, idx) => {
    body.push(row(i));
    const next = items[idx + 1];
    const groupEnds = !next || !next.upsell || (i.upsell ? next.upsell_for !== i.upsell_for : next.upsell_for !== i.product_id);
    if (!groupEnds) return;
    const m = i.upsell ? mains.find((x) => x.product_id && x.product_id === i.upsell_for) : i;
    if (m && !m.upsell && upFor === m.key) body.push(
      <div key={`${m.key}-up`} className="gi-upsearch">
        <ProductSearch products={products} autoFocus placeholder={`Допродаж до «${m.name}»: назва або артикул…`}
          exclude={inOrder} prefer={(p) => !!p.upsell && (!p.upsell_for?.length || p.upsell_for.includes(m.product_id!))}
          onPick={(x) => x && addUpsell(m, x)} onCancel={() => setUpFor(null)} />
      </div>);
  });

  return (
    <div className="goods">
      {body}
      {!readOnly && (<>
        <ProductSearch inputRef={search} products={products} free placeholder="Додати товар: назва, артикул або штрихкод" onPick={addMain} big={!items.length} autoFocus={autoFocusSearch && !items.length} />
        {offers.length > 0 && (
          <div className="gi-offers">
            <Sparkles size={15} aria-hidden />
            <span className="gi-offers-l">Часто беруть разом</span>
            <span className="gi-offers-list">
              {offers.map((p) => (
                <button key={p.id} type="button" className="gi-offer" title={`Додати допродажем: ${p.name}`}
                  onClick={() => addUpsell(mainProducts.find((m) => p.upsell_for?.includes(m.product_id!)) ?? mainProducts[0], { p })}>
                  <Plus size={13} /><span className="ell">{p.name}</span><b>{money(p.sale_price ?? p.price)} ₴</b>
                </button>
              ))}
            </span>
          </div>
        )}
      </>)}
    </div>
  );
});

/** Пошук товару (з варіантами) зі списком під полем; Enter / стрілки. free — довільна позиція без товару зі складу. */
export function ProductSearch({ products, onPick, placeholder, free = false, autoFocus = false, onCancel, exclude, prefer, inputRef, big }: {
  products: Product[]; onPick: (x?: Pick, text?: string) => void; placeholder: string; free?: boolean; autoFocus?: boolean; onCancel?: () => void;
  exclude?: Set<number>; prefer?: (p: Product) => boolean; inputRef?: React.RefObject<HTMLInputElement | null>; big?: boolean;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(autoFocus);
  const [hl, setHl] = useState(0);
  const list = useMemo(() => {
    const t = q.trim().toLowerCase();
    const rows: Pick[] = [];
    const pool = products.filter((p) => !exclude?.has(p.id));
    if (prefer) pool.sort((a, b) => Number(prefer(b)) - Number(prefer(a)));
    for (const p of pool) {
      const vs = (p.variants ?? []).filter((v) => v.active);
      const bar = (p as { barcode?: string }).barcode ?? "";
      if (vs.length) {
        for (const v of vs) if (!t || `${p.name} ${v.name} ${p.sku} ${v.sku} ${bar}`.toLowerCase().includes(t)) rows.push({ p, v });
      } else if (!t || `${p.name} ${p.sku} ${bar}`.toLowerCase().includes(t)) rows.push({ p });
      if (rows.length >= 40) break;
    }
    return rows;
  }, [q, products, exclude, prefer]);
  const n = list.length + (free && q.trim() ? 1 : 0);
  const pick = (x?: Pick) => { onPick(x, q.trim()); setQ(""); setHl(0); setOpen(false); };
  return (
    <div className={`psearch ac${big ? " big" : ""}`}>
      <Search size={15} className="psearch-ic" aria-hidden />
      <input ref={inputRef} value={q} placeholder={placeholder} autoFocus={autoFocus} aria-label={placeholder}
        onChange={(e) => { setQ(e.target.value); setHl(0); setOpen(true); }}
        onFocus={() => setOpen(true)} onBlur={() => setTimeout(() => { setOpen(false); if (!q.trim()) onCancel?.(); }, 150)}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown") { e.preventDefault(); setHl((h) => (h + 1) % Math.max(n, 1)); }
          else if (e.key === "ArrowUp") { e.preventDefault(); setHl((h) => (h - 1 + n) % Math.max(n, 1)); }
          else if (e.key === "Enter") { e.preventDefault(); if (hl < list.length) pick(list[hl]); else if (free && q.trim()) pick(); }
          else if (e.key === "Escape") { e.preventDefault(); e.stopPropagation(); setOpen(false); onCancel?.(); }
        }} />
      {open && n > 0 && (
        <div className="ac-list on">
          {list.map(({ p, v }, i) => (
            <div key={`${p.id}-${v?.id ?? 0}`} className={`goods-opt ${i === hl ? "hl" : ""}`} onMouseDown={(e) => { e.preventDefault(); pick({ p, v }); }}>
              {p.photo ? <img src={`${ROOT}${p.photo}`} alt="" /> : <span className="ph"><Package size={14} /></span>}
              <span className="nm">{p.name}{v && <b> · {v.name}</b>}{p.upsell && <span className="badge info">допродаж</span>}{p.discount_percent > 0 && <span className="badge warn">−{p.discount_percent}%</span>}</span>
              <small>{money(v?.price ?? p.sale_price ?? p.price)} ₴ · {(v ?? p).available} шт</small>
            </div>
          ))}
          {free && q.trim() && (
            <div className={hl === list.length ? "hl" : ""} onMouseDown={(e) => { e.preventDefault(); pick(); }}>
              <span>Довільна позиція «{q.trim()}»</span><small>Enter</small>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
