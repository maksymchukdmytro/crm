// Видаткові накладні (UI-DESIGN §6, макет 08): реєстр виданих документів, юрособа в кожному рядку, три кнопки документів.
import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, ChevronDown, Download, FileText, Printer, Receipt, RefreshCw, Search, ShieldCheck } from "lucide-react";
import { api, qs, ROOT } from "../lib/api";
import { errText, useDebounced, useMeta, useToast } from "../lib/app";
import { money } from "../lib/format";
import { DOC_OF, printDocument, printIssued, printMany } from "../lib/docs";
import { BulkBar, Button, ChipSelect, DenseTable, IconButton, MenuButton, MobileActs, Tabs, Tag, type DenseCol } from "../components/ui";
import { SOURCE_COLORS } from "./Orders";
import OrderModal from "./OrderCard";

type Row = {
  id: number; number_text: string; issued_at: string | null; order_id: number | null; customer: string; total: number; state: "active" | "void";
  entity_id: number | null; entity: string; changed: boolean; print_count: number; docs: { waybill?: number | null; invoice?: number | null; warranty?: number | null };
};
type List = { rows: Row[]; total: number; sum: number; count_active: number; entities: { id: number; name: string; count: number }[]; all: number };

const monthName = (p: string) => new Date(`${p}-15T12:00:00`).toLocaleDateString("uk-UA", { month: "long", year: "numeric" }).replace(/^./, (c) => c.toUpperCase()).replace(" р.", "");
const curMonth = () => new Date().toISOString().slice(0, 7);

export default function InvoicesPage() {
  const meta = useMeta();
  const toast = useToast();
  const qc = useQueryClient();
  const [sp, setSp] = useSearchParams();
  const period = sp.get("period") || curMonth();
  const entity = sp.get("entity") || "";
  const hasInvoice = sp.get("inv") || "";
  const status = sp.get("status") || "";
  const [search, setSearch] = useState(sp.get("q") || "");
  const dq = useDebounced(search, 300);
  const [open, setOpen] = useState<number | null>(null);
  const [sel, setSel] = useState<Set<number>>(new Set());
  const set = (patch: Record<string, string>) => { const n = new URLSearchParams(sp); Object.entries(patch).forEach(([k, v]) => (v ? n.set(k, v) : n.delete(k))); setSp(n, { replace: true }); };
  const params = { period, entity: entity || undefined, has_invoice: hasInvoice || undefined, status: status || undefined, q: dq || undefined };
  const q = useQuery({ queryKey: ["documents", params], queryFn: () => api.get<List>(`/documents${qs(params)}`) });
  const rows = q.data?.rows ?? [];
  const colors = useMemo(() => Object.fromEntries(meta.legal_entities.map((e, i) => [e.id, SOURCE_COLORS[i % SOURCE_COLORS.length]])), [meta.legal_entities]);
  const err = (m: string) => toast(m, "error");
  const refresh = () => qc.invalidateQueries({ queryKey: ["documents"] });

  const reissue = useMutation({
    mutationFn: (id: number) => api.post<{ id: number; number_text: string }>(`/documents/${id}/reissue`),
    onSuccess: (d) => { refresh(); toast(`Перевипущено: ${d.number_text}`, "ok", { action: { label: "Друк", onClick: () => printIssued(d.id, err) } }); },
    onError: (e) => toast(errText(e), "error"),
  });

  const months = Array.from({ length: 12 }, (_, i) => { const d = new Date(); d.setDate(15); d.setMonth(d.getMonth() - i); return d.toISOString().slice(0, 7); });
  const tabs = [{ key: "", label: "Усі юрособи", count: q.data?.all ?? null },
    ...(q.data?.entities ?? meta.legal_entities.map((e) => ({ id: e.id, name: e.name, count: 0 }))).map((e) => ({ key: String(e.id), label: e.name, count: e.count }))];

  const docBtn = (r: Row, kind: "waybill" | "invoice" | "warranty") => {
    const id = r.docs[kind];
    const Icon = kind === "waybill" ? FileText : kind === "invoice" ? Receipt : ShieldCheck;
    const label = kind === "waybill" ? "Накладна" : kind === "invoice" ? "Рахунок" : "Гарантія";
    if (!id && kind === "invoice") return <button key={kind} type="button" className="doc-pill off" disabled title="Рахунок не виставлявся"><Icon size={13} />{label}</button>;
    return (
      <span key={kind} className="doc-pill-wrap">
        <button type="button" className="doc-pill" onClick={() => (id ? printIssued(id, err) : r.order_id && printDocument(DOC_OF[kind], r.order_id, err).then(refresh))}
          title={id ? "Відкрити PDF" : "Видати й відкрити"}><Icon size={13} />{label}</button>
        {id && (
          <MenuButton className="doc-more" button={({ open: o, toggle }) => <button type="button" className="doc-arrow" aria-label={`${label}: ще`} aria-expanded={o} onClick={toggle}><ChevronDown size={12} /></button>}>
            {(close) => (<>
              <button className="pop-item" onClick={() => { close(); printIssued(id, err, true); }}><Download size={15} />Завантажити</button>
              <button className="pop-item" onClick={() => { close(); if (window.confirm("Перевипустити документ? Старий буде анульовано, новий отримає новий номер.")) reissue.mutate(id); }}><RefreshCw size={15} />Перевипустити</button>
            </>)}
          </MenuButton>
        )}
      </span>
    );
  };

  const COLS: DenseCol<Row>[] = [
    { key: "num", mobile: "title", label: "№ накладної", width: "96px", render: (r) => <span className={`mono doc-num${r.state === "void" ? " void" : ""}`}>{r.number_text}</span> },
    { key: "date", mobile: "sub", label: "Дата", width: "48px", render: (r) => <span className="num muted">{r.issued_at ? new Date(r.issued_at).toLocaleDateString("uk-UA", { day: "2-digit", month: "2-digit" }) : ""}</span> },
    { key: "order", mobile: "sub", label: "Замовл.", width: "62px", render: (r) => r.order_id ? <button type="button" className="link-btn" onClick={() => setOpen(r.order_id)}>№{r.order_id}</button> : <span className="muted">—</span> },
    { key: "buyer", mobile: "title", label: "Покупець", width: "minmax(110px, 1.2fr)", title: (r) => r.customer, render: (r) => (
      <span className="o-cust"><span className="ell">{r.customer || "—"}</span>
        {r.state === "void" && <Tag>Анульовано</Tag>}
        {r.changed && <Tag kind="warn" title="Замовлення змінилось після видачі документа">змінилось</Tag>}</span>
    ) },
    { key: "entity", mobile: "sub", label: "Юрособа", width: "minmax(110px, 1fr)", render: (r) => <span className="o-dot-txt"><i style={{ background: colors[r.entity_id ?? 0] ?? "var(--faint)" }} /><span className="ell">{r.entity || "—"}</span></span> },
    { key: "sum", mobile: "end", label: "Сума", width: "84px", align: "right", render: (r) => <b className="num">{money(r.total)} ₴</b> },
    { key: "fix", mobile: "sub", label: "", width: "28px", align: "center", render: (r) => r.changed && r.state === "active"
      ? <IconButton size={28} icon={RefreshCw} label="Перевипустити" className="doc-reissue" onClick={() => reissue.mutate(r.id)} /> : null },
    { key: "docs", mobile: "sub", label: "Документи", width: "356px", align: "right", render: (r) => <span className="doc-pills">{docBtn(r, "waybill")}{docBtn(r, "invoice")}{docBtn(r, "warranty")}</span> },
  ];

  // телефон (мобільна v2): номер і позначки, дата·замовлення; покупець і сума; юрособа; три кнопки документів
  const mobileCard = (r: Row) => (<>
    <div className="mc-top">
      <span className={`mi-no${r.state === "void" ? " doc-num void" : ""}`}>{r.number_text}</span>
      {r.state === "void" && <Tag>Анульовано</Tag>}
      {r.changed && <Tag kind="warn" title="Замовлення змінилось після видачі документа">змінилось</Tag>}
      <span className="mc-meta">{r.issued_at ? new Date(r.issued_at).toLocaleDateString("uk-UA", { day: "2-digit", month: "2-digit" }) : ""}
        {r.order_id && <> · <button type="button" className="link-btn" onClick={() => setOpen(r.order_id)}>№{r.order_id}</button></>}</span>
    </div>
    <div className="mc-name"><b>{r.customer || "—"}</b><span className="sum">{money(r.total)} <small>₴</small></span></div>
    <div className="mi-ent"><i style={{ background: colors[r.entity_id ?? 0] ?? "var(--faint)" }} />{r.entity || "без юрособи"}
      {r.changed && r.state === "active" && <button type="button" className="link-btn" style={{ marginLeft: "auto" }} onClick={() => reissue.mutate(r.id)}><RefreshCw size={13} />Перевипустити</button>}</div>
    <div className="mi-docs m-stop"><span className="doc-pills">{docBtn(r, "waybill")}{docBtn(r, "invoice")}{docBtn(r, "warranty")}</span></div>
  </>);

  const exportUrl = `${ROOT}/api/documents/export${qs(params)}`;
  const selRows = rows.filter((r) => sel.has(r.id) && r.state === "active");

  return (
    <div className="page-list page-invoices">
      <div className="list-head">
        <h1>Видаткові накладні</h1>
        <span className="list-sum">{monthName(period.slice(0, 7))} · <b>{q.data?.count_active ?? 0}</b> накладних · <b>{money(q.data?.sum ?? 0)} ₴</b></span>
        <div className="list-acts">
          <MenuButton button={({ open: o, toggle }) => <button className="btn" aria-expanded={o} onClick={toggle}><CalendarDays size={15} />{monthName(period.slice(0, 7))}<ChevronDown size={14} /></button>}>
            {(close) => months.map((m) => <button key={m} className={`pop-item${m === period ? " on" : ""}`} onClick={() => { set({ period: m === curMonth() ? "" : m }); close(); }}>{monthName(m)}</button>)}
          </MenuButton>
          <a className="btn" href={exportUrl}><Download size={15} />Експорт реєстру</a>
        </div>
      </div>
      <MobileActs>
        <MenuButton button={({ open: o, toggle }) => <button type="button" className="rb" aria-label={`Місяць: ${monthName(period.slice(0, 7))}`} aria-expanded={o} onClick={toggle}><CalendarDays size={20} /></button>}>
          {(close) => months.map((m) => <button key={m} className={`pop-item${m === period ? " on" : ""}`} onClick={() => { set({ period: m === curMonth() ? "" : m }); close(); }}>{monthName(m)}</button>)}
        </MenuButton>
      </MobileActs>
      <Tabs items={tabs} value={entity} onChange={(k) => set({ entity: k })} label="Юрособи" className="list-tabs" />
      <div className="chips-row">
        <ChipSelect label="Статус замовлення" value={status ? status.split(",") : []} onChange={(v) => set({ status: v.join(",") })}
          options={meta.statuses.filter((s) => s.active && (s.stage ?? "order") === "order").map((s) => ({ value: String(s.id), label: s.name, color: s.color }))} />
        <ChipSelect label="Є рахунок-фактура" single search={false} value={hasInvoice ? ["1"] : []} onChange={(v) => set({ inv: v[0] ?? "" })}
          options={[{ value: "1", label: "Лише з рахунком-фактурою" }]} />
        <label className="list-search">
          <Search size={15} aria-hidden />
          <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="№ накладної, замовлення або покупець" aria-label="Пошук накладних" />
        </label>
      </div>
      <DenseTable<Row> label="Видаткові накладні" rows={rows} cols={COLS} rowKey={(r) => r.id} isLoading={q.isLoading}
        selected={sel} onSelect={setSel} onOpen={(r) => printIssued(r.id, err)}
        rowClass={(r) => (r.state === "void" ? "void" : "")}
        mobileCard={mobileCard}
        empty={<div className="empty-state"><p>За {monthName(period.slice(0, 7)).toLowerCase()} накладних ще немає. Вони з'являються, коли замовлення стає «Відправленим» або при першому друці.</p></div>} />
      <p className="hint inv-foot">Юрособа — у кожному рядку й кольоровою міткою; вкладки зверху лише звужують список. Неактивний «Рахунок» — рахунок-фактуру не виставляли.</p>

      <BulkBar count={sel.size} onClear={() => setSel(new Set())}
        primary={<Button variant="primary" icon={Printer} disabled={!selRows.length} onClick={() => printMany(selRows.map((r) => r.id), err)}>Друкувати накладні ({selRows.length})</Button>}>
        <button className="btn quiet sm" onClick={async () => { for (const r of selRows) await printIssued(r.id, err, true); }}><Download size={14} />Завантажити PDF</button>
        <a className="btn quiet sm" href={exportUrl}><Download size={14} />Експорт реєстру</a>
      </BulkBar>
      {open && <OrderModal id={String(open)} onClose={() => { setOpen(null); refresh(); }} onOpen={(oid) => setOpen(oid)} />}
    </div>
  );
}
