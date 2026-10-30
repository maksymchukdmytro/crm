// Друковані документи замовлення: видаткова накладна, рахунок-фактура, гарантійний талон.
// Шаблон видаткової — з сервісу mdmy.me/nakladna (pdfmake + шрифт Inter): багато повітря, заокруглені картки,
// фірмовий колір лише в акцентах. Рахунок-фактура й гарантійний талон зібрані з тих самих блоків.
// PDF збирає браузер; pdfmake і шрифт вантажаться лише при першому друці (окремий файл).
import { ROOT } from "./api";
import type { Documents } from "./types";

type Doc = Documents & { number_text?: string };
type Item = Doc["order"]["items"][number];
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Node = any;

// ---------------------------------------------------------------- сума прописом
const ONES_M = ["", "один", "два", "три", "чотири", "п'ять", "шість", "сім", "вісім", "дев'ять"];
const ONES_F = ["", "одна", "дві", "три", "чотири", "п'ять", "шість", "сім", "вісім", "дев'ять"];
const TEENS = ["десять", "одинадцять", "дванадцять", "тринадцять", "чотирнадцять", "п'ятнадцять", "шістнадцять", "сімнадцять", "вісімнадцять", "дев'ятнадцять"];
const TENS = ["", "", "двадцять", "тридцять", "сорок", "п'ятдесят", "шістдесят", "сімдесят", "вісімдесят", "дев'яносто"];
const HUNDREDS = ["", "сто", "двісті", "триста", "чотириста", "п'ятсот", "шістсот", "сімсот", "вісімсот", "дев'ятсот"];
const SCALES: [string[], boolean][] = [[["", "", ""], true], [["тисяча", "тисячі", "тисяч"], true],
  [["мільйон", "мільйони", "мільйонів"], false], [["мільярд", "мільярди", "мільярдів"], false]];

export function plural(n: number, f: string[]) {
  n = Math.abs(n) % 100; if (n >= 11 && n <= 19) return f[2];
  n = n % 10; return n === 1 ? f[0] : n >= 2 && n <= 4 ? f[1] : f[2];
}
function triad(n: number, fem: boolean) {
  const w: string[] = [], h = Math.floor(n / 100), r = n % 100;
  if (h) w.push(HUNDREDS[h]);
  if (r >= 10 && r <= 19) w.push(TEENS[r - 10]);
  else { const t = Math.floor(r / 10), o = r % 10; if (t) w.push(TENS[t]); if (o) w.push((fem ? ONES_F : ONES_M)[o]); }
  return w;
}
export function amountInWords(sum: number) {
  const cents = Math.round(sum * 100), hr = Math.floor(cents / 100), kop = cents % 100;
  let words: string[] = [];
  if (!hr) words = ["нуль"];
  else for (let n = hr, i = 0; n; n = Math.floor(n / 1000), i++) {
    const part = n % 1000; if (!part) continue;
    const [forms, fem] = SCALES[i], chunk = triad(part, fem);
    if (i) chunk.push(plural(part, forms));
    words = chunk.concat(words);
  }
  const t = words.join(" ");
  return `${t[0].toUpperCase()}${t.slice(1)} ${plural(hr, ["гривня", "гривні", "гривень"])} ` +
    `${String(kop).padStart(2, "0")} ${plural(kop, ["копійка", "копійки", "копійок"])}`;
}

// ---------------------------------------------------------------- форматування
const round2 = (n: number) => Math.round((+n || 0) * 100) / 100;
const money = (n: number) => round2(n).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, " ").replace(".", ",");
const qtyStr = (n: number) => (Number.isInteger(+n) ? String(+n) : String(round2(n)).replace(".", ","));
const MONTHS = ["січня", "лютого", "березня", "квітня", "травня", "червня", "липня", "серпня", "вересня", "жовтня", "листопада", "грудня"];
function dateLong(iso: string) {
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || ""); if (!m) return "";
  return `${+m[3]} ${MONTHS[+m[2] - 1]} ${m[1]} р.`;
}
const lineSum = (it: Item) => round2((+it.qty || 0) * (+it.price || 0));
const phoneFmt = (p: string) => { const d = (p || "").replace(/\D/g, ""); return d.length === 12 ? `+${d.slice(0, 2)} ${d.slice(2, 5)} ${d.slice(5, 8)} ${d.slice(8, 10)} ${d.slice(10)}` : p; };

// ---------------------------------------------------------------- стиль (як у mdmy)
const INK = "#111318", TEXT = "#2B2F36", MUTED = "#7A808A", FAINT = "#A9AEB6", HAIR = "#ECEEF1", LABEL = "#4B515B";
const hex = (c: string) => (/^#[0-9a-f]{6}$/i.test(c || "") ? c : "#C1D0E4");
function tint(c: string, k: number) {
  const n = parseInt(hex(c).slice(1), 16), mix = (v: number) => Math.round(v + (255 - v) * k);
  return "#" + [n >> 16, (n >> 8) & 255, n & 255].map((v) => mix(v).toString(16).padStart(2, "0")).join("");
}
const NUM = { fontFeatures: ["tnum"] };
const M = 44, W = 595.28 - 2 * M;
const small = (t: string, extra?: object) => ({ text: t, fontSize: 8, color: MUTED, ...extra });
const lbl = (t: string, extra?: object) => ({ text: t, font: "InterM", fontSize: 8.5, color: LABEL, ...extra });
const linesOf = (t: string, perLine: number) => Math.max(1, Math.ceil(String(t || "").length / perLine));

function rounded(width: number, height: number, color: string, content: Node[], pad: number[] = [16, 14]): Node {
  return { width, stack: [
    { canvas: [{ type: "rect", x: 0, y: 0, w: width, h: height, r: 12, color }], relativePosition: { x: 0, y: 0 } },
    { table: { widths: ["*"], heights: [height], body: [[{ stack: content }]] },
      layout: { hLineWidth: () => 0, vLineWidth: () => 0, paddingLeft: () => pad[0], paddingRight: () => pad[0], paddingTop: () => pad[1], paddingBottom: () => 0 } },
  ] };
}

function theme(d: Doc) {
  const ACCENT = hex(d.docs.doc_accent);
  const n = parseInt(ACCENT.slice(1), 16), lum = (0.2126 * (n >> 16) + 0.7152 * ((n >> 8) & 255) + 0.0722 * (n & 255)) / 255;
  const LIGHT = lum > 0.62;
  return { ACCENT, ON: LIGHT ? INK : "#FFFFFF", SOFT: tint(ACCENT, LIGHT ? 0.62 : 0.94) };
}

function header(d: Doc, title: string, number: string, sub: string, mb = 30): Node {
  const s = d.seller;
  const brand = d.docs.doc_logo ? { image: d.docs.doc_logo, fit: [150, 46] } : { text: s.name || "", font: "Display", fontSize: 15, color: INK };
  return { columns: [
    { width: "*", stack: [brand] },
    { width: "auto", stack: [
      lbl(title, { alignment: "right" }),
      { text: number, font: "Display", fontSize: 24, color: INK, alignment: "right", margin: [0, 2, 0, 4] },
      small(sub, { alignment: "right" }),
    ] },
  ], margin: [0, 0, 0, mb] };
}

function sellerRows(d: Doc, short = false) {
  const s = d.seller;
  const bank = short ? [] : [s.iban ? `IBAN ${s.iban}` : "", s.bank];  // у рахунку IBAN і банк — у «Реквізитах для оплати», у талоні не потрібні
  return [s.code ? `${s.code_label || "РНОКПП"} ${s.code}` : "", s.address, ...bank, s.phone].filter(Boolean) as string[];
}
function buyerRows(d: Doc) {
  const o = d.order;
  const deliv = [o.delivery, o.ttn ? `ТТН ${o.ttn}` : ""].filter(Boolean).join(" · ");
  return [phoneFmt(o.phone), o.email, deliv, o.address].filter(Boolean) as string[];
}

function parties(d: Doc, left: [string, string, string[]], right: [string, string, string[]], mb = 26): Node {
  const { SOFT } = theme(d);
  const cw = (W - 12) / 2, PER = 44;
  const rowsH = (rows: string[]) => rows.reduce((h, r) => h + linesOf(r, PER) * 13.8, 0);
  const nameH = (t: string) => linesOf(t, 30) * 16.5;
  const cardH = Math.max(rowsH(left[2]) + nameH(left[1]), rowsH(right[2]) + nameH(right[1])) + 56;
  const card = ([label, name, rows]: [string, string, string[]]) => rounded(cw, cardH, SOFT, [
    lbl(label, { margin: [0, 0, 0, 7] }),
    { text: name || "—", font: "InterM", fontSize: 11, color: INK, margin: [0, 0, 0, 4] },
    ...rows.map((r) => ({ text: r, fontSize: 8.5, color: TEXT, lineHeight: 1.3 })),
  ]);
  return { columns: [card(left), card(right)], columnGap: 12, margin: [0, 0, 0, mb] };
}

const th = (t: string, al = "left") => ({ text: t, font: "InterM", fontSize: 8.5, color: LABEL, alignment: al });
const tableLayout = {
  hLineWidth: (i: number, node: Node) => (i === 0 ? 0 : i === node.table.body.length ? 0 : i === 1 ? 1 : 0.6),
  hLineColor: (i: number) => (i === 1 ? "#C9CDD3" : HAIR),
  vLineWidth: () => 0, paddingLeft: (i: number) => (i === 0 ? 0 : 8), paddingRight: (i: number, node: Node) => (i === node.table.widths.length - 1 ? 0 : 8),
  paddingTop: (r: number) => (r === 0 ? 0 : 11), paddingBottom: (r: number) => (r === 0 ? 8 : 11),
};
const nameCell = (it: Item) => ({ stack: [{ text: it.name || "", font: "InterM", fontSize: 9.5, color: INK }]
  .concat(it.sku ? [{ text: it.sku, fontSize: 7.5, color: MUTED, margin: [0, 2, 0, 0] } as Node] : []) });

function itemsTable(d: Doc): Node {
  const unit = d.docs.doc_unit || "шт.";
  const body: Node[] = [[th("Товар"), th("К-сть", "right"), th("Ціна", "right"), th("Сума", "right")]];
  d.order.items.forEach((it) => body.push([
    nameCell(it),
    { text: `${qtyStr(it.qty)} ${unit}`, alignment: "right", color: TEXT, ...NUM },
    { text: money(it.price), alignment: "right", color: TEXT, ...NUM },
    { text: money(lineSum(it)), alignment: "right", font: "InterM", color: INK, ...NUM },
  ]));
  return { table: { headerRows: 1, widths: ["*", 56, 70, 78], body }, layout: tableLayout };
}

function totalsBlock(d: Doc, payLabel: string, mb = 34): Node {
  const { ACCENT, ON } = theme(d);
  const subtotal = round2(d.order.items.reduce((s, it) => s + lineSum(it), 0));
  const disc = round2(d.order.discount || 0);
  const sum = round2(subtotal - disc);
  const vat = (d.seller.vat_note || "Без ПДВ").trim();
  const noVat = /^без/i.test(vat);
  const TW = 230;
  const rows: Node[] = [{ columns: [lbl("Разом"), { text: money(subtotal) + " грн", alignment: "right", fontSize: 9, color: TEXT, ...NUM }], margin: [16, 0, 16, 5] }];
  if (disc > 0) rows.push({ columns: [lbl("Знижка"), { text: "−" + money(disc) + " грн", alignment: "right", fontSize: 9, color: TEXT, ...NUM }], margin: [16, 0, 16, 5] });
  rows.push({ columns: [lbl("ПДВ"), small(noVat ? "без ПДВ" : vat, { alignment: "right" })], margin: [16, 0, 16, 10] });
  const big = money(sum) + " грн";
  const fs = big.length > 15 ? 13 : big.length > 12 ? 15 : 18;
  rows.push(rounded(TW, 50, ACCENT, [{ columns: [
    { text: payLabel, width: 62, fontSize: 9, color: ON, noWrap: true, margin: [0, 6, 0, 0] },
    { text: big, width: "*", font: "Display", fontSize: fs, color: ON, alignment: "right", noWrap: true, margin: [0, (18 - fs) / 2, 0, 0], ...NUM },
  ] }], [16, 13]));
  const words = { width: "*", stack: [
    lbl("Сума прописом", { margin: [0, 0, 0, 4] }),
    { text: amountInWords(sum), font: "InterM", fontSize: 9.5, color: INK },
    small(`${vat.charAt(0).toUpperCase() + vat.slice(1)} · ${d.order.items.length} ${plural(d.order.items.length, ["позиція", "позиції", "позицій"])}`, { margin: [0, 4, 0, 0] }),
  ] };
  return { columns: [words, { width: TW, stack: rows }], columnGap: 30, margin: [0, 0, 0, mb] };
}

const hairline = (mb = 18): Node => ({ canvas: [{ type: "line", x1: 0, y1: 0, x2: W, y2: 0, lineWidth: 0.6, lineColor: HAIR }], margin: [0, 0, 0, mb] });

function signatures(left: [string, string], right: [string, string] | null, top = 34): Node {
  const sig = ([label, name]: [string, string]) => ({ width: "*", stack: [
    { canvas: [{ type: "line", x1: 0, y1: 0, x2: (W - 40) / 2, y2: 0, lineWidth: 0.8, lineColor: "#D5D8DD" }], margin: [0, top, 0, 6] },
    lbl(label), { text: name || " ", fontSize: 8.5, color: TEXT, margin: [0, 2, 0, 0] },
  ] });
  return { columns: [sig(left), right ? sig(right) : { width: "*", text: "" }], columnGap: 40, unbreakable: true };
}

function page(d: Doc, title: string, content: Node[]): Node {
  const footLeft = [d.docs.doc_site, d.docs.doc_note].filter(Boolean).join("  ·  ");
  return {
    pageSize: "A4", pageMargins: [M, 46, M, 56],
    info: { title, author: d.seller.name || "" },
    defaultStyle: { font: "Inter", fontSize: 9, color: TEXT, lineHeight: 1.2 },
    footer: (p: number, pages: number) => ({ margin: [M, 18, M, 0], columns: [
      small(footLeft, { fontSize: 7.5, color: FAINT }),
      small(pages > 1 ? `${p} / ${pages}` : "", { fontSize: 7.5, color: FAINT, alignment: "right" }),
    ] }),
    content,
  };
}

// ---------------------------------------------------------------- 1. Видаткова накладна (як у mdmy)
export function nakladna(d: Doc): Node {
  const number = d.number_text || (d.docs.doc_prefix || "") + d.order.id;
  return page(d, `Видаткова накладна ${number}`, [
    header(d, "Видаткова накладна", number, [dateLong(d.order.date), `замовлення № ${d.order.id}`].join("  ·  ")),
    parties(d, ["Постачальник", d.seller.name, sellerRows(d)], ["Одержувач", d.order.buyer, buyerRows(d)]),
    itemsTable(d),
    hairline(),
    totalsBlock(d, "До сплати"),
    signatures(["Відвантажив(ла)", d.seller.signer], ["Отримав(ла)", d.order.buyer]),
  ]);
}

// ---------------------------------------------------------------- 2. Рахунок-фактура: документ на оплату з реквізитами
export function rahunok(d: Doc): Node {
  const { SOFT } = theme(d);
  const number = d.number_text || (d.docs.invoice_prefix || "") + d.order.id;
  const days = Number(d.docs.invoice_days || 0);
  const vat = (d.seller.vat_note || "Без ПДВ").trim();
  const sum = round2(d.order.items.reduce((s, it) => s + lineSum(it), 0) - (d.order.discount || 0));
  const purpose = `Оплата за рахунком № ${number} від ${dateLong(d.order.date)}, ${vat.toLowerCase().startsWith("без") ? "без ПДВ" : vat}`;
  const kv = (k: string, v: string) => ({ columns: [{ ...lbl(k), width: 110 }, { text: v || "—", width: "*", fontSize: 9, color: INK, font: "InterM", ...NUM }], margin: [0, 0, 0, 5] });
  const payRows = [kv("Отримувач", d.seller.name), kv(d.seller.code_label || "РНОКПП", d.seller.code), kv("IBAN", d.seller.iban),
    kv("Банк", d.seller.bank), kv("Сума", money(sum) + " грн"), kv("Призначення", purpose)];
  const pay = rounded(W, 34 + 6 * 19 + (purpose.length > 70 ? 12 : 0), SOFT, [lbl("Реквізити для оплати", { margin: [0, 0, 0, 9] }), ...payRows]);
  return page(d, `Рахунок-фактура ${number}`, [
    header(d, "Рахунок-фактура", number, [dateLong(d.order.date), `замовлення № ${d.order.id}`].join("  ·  "), 24),
    parties(d, ["Постачальник", d.seller.name, sellerRows(d, true)], ["Платник", d.order.buyer, [phoneFmt(d.order.phone), d.order.email].filter(Boolean) as string[]], 20),
    itemsTable(d),
    hairline(16),
    totalsBlock(d, "До оплати", 20),
    { ...pay, margin: [0, 0, 0, 12] },
    small(days > 0 ? `Рахунок дійсний до оплати протягом ${days} ${plural(days, ["банківського дня", "банківських днів", "банківських днів"])}. Оплата цього рахунку означає згоду з умовами поставки товару.`
      : "Оплата цього рахунку означає згоду з умовами поставки товару.", { margin: [0, 0, 0, 6] }),
    signatures(["Виписав(ла)", d.seller.signer], null, 26),
  ]);
}

// ---------------------------------------------------------------- 3. Гарантійний талон
export function garantiya(d: Doc): Node {
  const { SOFT, ACCENT, ON } = theme(d);
  const number = d.number_text || (d.docs.warranty_prefix || "") + d.order.id;
  const def = Number(d.docs.warranty_months || 12);
  const unit = d.docs.doc_unit || "шт.";
  const months = (it: Item) => it.warranty_months || def;
  const body: Node[] = [[th("Товар"), th("К-сть", "right"), th("Серійний номер"), th("Гарантія", "right")]];
  d.order.items.forEach((it) => body.push([
    nameCell(it),
    { text: `${qtyStr(it.qty)} ${unit}`, alignment: "right", color: TEXT, ...NUM },
    { canvas: [{ type: "line", x1: 0, y1: 12, x2: 112, y2: 12, lineWidth: 0.6, lineColor: "#C9CDD3" }] },
    { text: `${months(it)} ${plural(months(it), ["місяць", "місяці", "місяців"])}`, alignment: "right", font: "InterM", color: INK, ...NUM },
  ]));
  const terms = (d.docs.warranty_terms || "").split(/\n+/).map((t) => t.trim()).filter(Boolean).map((t) => t.replace(/\{months\}/g, String(def)));
  const sale = { columns: [
    rounded(W * 0.62, 50, SOFT, [{ columns: [
      { stack: [lbl("Дата продажу"), { text: dateLong(d.order.date), font: "InterM", fontSize: 11, color: INK, margin: [0, 3, 0, 0] }] },
      { stack: [lbl("Замовлення"), { text: `№ ${d.order.id}`, font: "InterM", fontSize: 11, color: INK, margin: [0, 3, 0, 0] }] },
    ] }], [16, 11]),
    rounded(W * 0.38 - 12, 50, ACCENT, [{ columns: [
      { text: "Гарантія", width: "auto", fontSize: 9, color: ON, margin: [0, 6, 0, 0] },
      { text: `${def} міс.`, width: "*", font: "Display", fontSize: 18, color: ON, alignment: "right" },
    ] }], [16, 13]),
  ], columnGap: 12, margin: [0, 0, 0, 18] };
  return page(d, `Гарантійний талон ${number}`, [
    header(d, "Гарантійний талон", number, `від ${dateLong(d.order.date)}`, 22),
    parties(d, ["Продавець", d.seller.name, sellerRows(d, true)], ["Покупець", d.order.buyer, [phoneFmt(d.order.phone), d.order.email].filter(Boolean) as string[]], 18),
    sale,
    { table: { headerRows: 1, widths: ["*", 50, 124, 74], body }, layout: tableLayout, margin: [0, 0, 0, 16] },
    lbl("Умови гарантійного обслуговування", { fontSize: 10, color: INK, margin: [0, 0, 0, 7] }),
    { ol: terms.map((t) => ({ text: t, fontSize: 8, color: TEXT, lineHeight: 1.25, margin: [0, 0, 0, 3] })), markerColor: MUTED, margin: [0, 0, 0, 8] },
    small("Товар отримав(ла) у справному стані, комплектність і зовнішній вигляд перевірив(ла), з умовами гарантії ознайомлений(а).", { color: TEXT, margin: [0, 4, 0, 0] }),
    signatures(["Продавець", d.seller.signer], ["Покупець", d.order.buyer], 26),
  ]);
}

// ---------------------------------------------------------------- друк
export const DOC_KINDS = {
  nakladna: { title: "Видаткова накладна", build: nakladna },
  rahunok: { title: "Рахунок-фактура", build: rahunok },
  garantiya: { title: "Гарантійний талон", build: garantiya },
} as const;
export type DocKind = keyof typeof DOC_KINDS;

let pdfLib: Promise<{ createPdf: (def: unknown) => { getBlob: (cb: (b: Blob) => void) => void } }> | null = null;
function loadPdf() {
  if (!pdfLib) pdfLib = (async () => {
    const pdfMake = (await import("pdfmake/build/pdfmake")).default;
    (window as unknown as { pdfMake: unknown }).pdfMake = pdfMake;
    await import("./vendor/inter-fonts.js");  // реєструє Inter (vfs + fonts) у window.pdfMake
    return pdfMake;
  })();
  return pdfLib;
}

export const KIND_OF: Record<DocKind, "waybill" | "invoice" | "warranty"> = { nakladna: "waybill", rahunok: "invoice", garantiya: "warranty" };
export const DOC_OF: Record<string, DocKind> = { waybill: "nakladna", invoice: "rahunok", warranty: "garantiya" };

async function postJson(url: string) {
  const r = await fetch(`${ROOT}${url}`, { method: "POST", credentials: "same-origin", headers: { "X-CRM": "1", "Content-Type": "application/json" } });
  if (!r.ok) {
    let msg = `Помилка ${r.status}`;
    try { const j = await r.json(); msg = j.error || j.detail || msg; } catch { /* */ }
    throw new Error(msg);
  }
  return r.json();
}

async function render(kind: DocKind, snap: Doc, w: Window | null) {
  if (!snap.order.items.length) throw new Error("У документі немає товарів");
  const pdfMake = await loadPdf();
  const blob = await new Promise<Blob>((res) => pdfMake.createPdf(DOC_KINDS[kind].build(snap)).getBlob(res));
  const url = URL.createObjectURL(blob);
  if (w) w.location.href = url; else window.location.href = url;
}

/** Видати документ замовлення (або взяти чинний) з номером і знімком даних, зібрати PDF і відкрити в новій вкладці. */
export async function printDocument(kind: DocKind, orderId: number, onError: (msg: string) => void) {
  const w = window.open("", "_blank");  // одразу — інакше браузер заблокує вікно після очікування
  try {
    const d = await postJson(`/api/orders/${orderId}/documents/${KIND_OF[kind]}`) as { id: number; snapshot: Doc };
    await render(kind, d.snapshot, w);
    postJson(`/api/documents/${d.id}/printed`).catch(() => undefined);
  } catch (e) {
    w?.close();
    onError((e as Error).message);
  }
}

/** Друк виданого документа з реєстру (за його знімком). */
export async function printIssued(docId: number, onError: (msg: string) => void, download = false) {
  const w = download ? null : window.open("", "_blank");
  try {
    const r = await fetch(`${ROOT}/api/documents/${docId}`, { credentials: "same-origin" });
    if (!r.ok) throw new Error(`Документ недоступний (${r.status})`);
    const d = await r.json() as { id: number; kind: string; number_text: string; snapshot: Doc };
    const kind = DOC_OF[d.kind];
    if (download) {
      const pdfMake = await loadPdf();
      const blob = await new Promise<Blob>((res) => pdfMake.createPdf(DOC_KINDS[kind].build(d.snapshot)).getBlob(res));
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob); a.download = `${d.number_text}.pdf`; a.click();
    } else await render(kind, d.snapshot, w);
    postJson(`/api/documents/${d.id}/printed`).catch(() => undefined);
  } catch (e) {
    w?.close();
    onError((e as Error).message);
  }
}

/** Кілька документів одним PDF (масовий друк накладних). */
export async function printMany(docIds: number[], onError: (msg: string) => void) {
  const w = window.open("", "_blank");
  try {
    const docs = await Promise.all(docIds.map((id) => fetch(`${ROOT}/api/documents/${id}`, { credentials: "same-origin" }).then((r) => r.json() as Promise<{ id: number; kind: string; snapshot: Doc }>)));
    const pdfMake = await loadPdf();
    const defs = docs.map((d) => DOC_KINDS[DOC_OF[d.kind]].build(d.snapshot));
    const merged = { ...defs[0], content: defs.flatMap((x, i) => (i ? [{ text: "", pageBreak: "before" }, ...x.content] : x.content)) };
    const blob = await new Promise<Blob>((res) => pdfMake.createPdf(merged).getBlob(res));
    const url = URL.createObjectURL(blob);
    if (w) w.location.href = url; else window.location.href = url;
    docs.forEach((d) => postJson(`/api/documents/${d.id}/printed`).catch(() => undefined));
  } catch (e) {
    w?.close();
    onError((e as Error).message);
  }
}

/** Старий друк без видачі номера (дані з поточного замовлення) — запасний. */
export async function printPreview(kind: DocKind, orderId: number, onError: (msg: string) => void) {
  const w = window.open("", "_blank");  // одразу — інакше браузер заблокує вікно після очікування
  try {
    const r = await fetch(`${ROOT}/api/orders/${orderId}/documents`, { credentials: "same-origin" });
    if (!r.ok) throw new Error(`Не вдалося отримати дані замовлення (${r.status})`);
    const d = (await r.json()) as Doc;
    if (!d.order.items.length) throw new Error("У замовленні немає товарів");
    const pdfMake = await loadPdf();
    const blob = await new Promise<Blob>((res) => pdfMake.createPdf(DOC_KINDS[kind].build(d)).getBlob(res));
    const url = URL.createObjectURL(blob);
    if (w) w.location.href = url; else window.location.href = url;
  } catch (e) {
    w?.close();
    onError((e as Error).message);
  }
}
