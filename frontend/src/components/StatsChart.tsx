// Графік статистики: стовпці за статусами (накопичувально) + лінія «Усі», підказка при наведенні,
// повзунок знизу для наближення частини періоду (як навігатор у LP-CRM). Чистий SVG, без бібліотек.
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

export type ChartPoint = { t: string; total: number; by_status: Record<string, number> };
export type ChartStatus = { id: number; name: string; color: string };

const MONTHS = ["січ", "лют", "бер", "кві", "тра", "чер", "лип", "сер", "вер", "жов", "лис", "гру"];
const MONTHS_FULL = ["Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень", "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"];
const DAYS = ["Неділя", "Понеділок", "Вівторок", "Середа", "Четвер", "П'ятниця", "Субота"];

const p2 = (n: number) => String(n).padStart(2, "0");
// «2026-10-29T14:00» → компоненти без перетворення поясу (сервер уже віддав місцевий час)
function parts(t: string) {
  const [d, hm = "00:00"] = t.split("T");
  const [y, m, dd] = d.split("-").map(Number);
  const [h] = hm.split(":").map(Number);
  return { y, m, d: dd, h, wd: new Date(y, m - 1, dd).getDay() };
}

export function axisLabel(t: string, group: string): string {
  const x = parts(t);
  if (group === "hour") return `${p2(x.h)}:00`;
  if (group === "month") return `${MONTHS[x.m - 1]} ${String(x.y).slice(2)}`;
  return `${p2(x.d)}.${p2(x.m)}`;
}

export function fullLabel(t: string, group: string): string {
  const x = parts(t);
  if (group === "hour") return `${p2(x.d)}.${p2(x.m)}.${x.y}, ${p2(x.h)}:00–${p2(x.h)}:59`;
  if (group === "month") return `${MONTHS_FULL[x.m - 1]} ${x.y}`;
  if (group === "week") {
    const a = new Date(x.y, x.m - 1, x.d), b = new Date(x.y, x.m - 1, x.d + 6);
    return `Тиждень ${p2(a.getDate())}.${p2(a.getMonth() + 1)} – ${p2(b.getDate())}.${p2(b.getMonth() + 1)}.${b.getFullYear()}`;
  }
  return `${DAYS[x.wd]}, ${p2(x.d)}.${p2(x.m)}.${x.y}`;
}

function niceMax(v: number): number {
  if (v <= 4) return 4;
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  for (const k of [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) if (k * p >= v) return k * p;
  return 10 * p;
}

function useWidth<T extends HTMLElement>(): [React.RefObject<T | null>, number] {
  const ref = useRef<T>(null);
  const [w, setW] = useState(800);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    setW(el.clientWidth || 800);
    const ro = new ResizeObserver(([e]) => setW(Math.max(280, Math.round(e.contentRect.width))));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, w];
}

export default function StatsChart({ points, statuses, hidden, showTotal, group, height = 300 }: {
  points: ChartPoint[]; statuses: ChartStatus[]; hidden: Set<number>; showTotal: boolean; group: string; height?: number;
}) {
  const [wrap, width] = useWidth<HTMLDivElement>();
  const n = points.length;
  const [range, setRange] = useState<[number, number]>([0, Math.max(0, n - 1)]);
  const key = `${n}:${points[0]?.t}:${points[n - 1]?.t}`;
  useEffect(() => setRange([0, Math.max(0, n - 1)]), [key, n]);
  const [a, b] = [Math.min(range[0], Math.max(0, n - 1)), Math.min(range[1], Math.max(0, n - 1))];
  const view = useMemo(() => points.slice(a, b + 1), [points, a, b]);
  const [hover, setHover] = useState<number | null>(null);

  const visible = statuses.filter((s) => !hidden.has(s.id));
  const L = 40, R = 12, T = 12, B = 26;
  const W = width, H = height;
  const pw = W - L - R, ph = H - T - B;
  const stackOf = (p: ChartPoint) => visible.reduce((acc, s) => acc + (p.by_status[String(s.id)] ?? 0), 0);
  const max = niceMax(Math.max(1, ...view.map((p) => Math.max(stackOf(p), showTotal ? p.total : 0))));
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((k) => Math.round(max * k * 100) / 100);
  const bw = pw / Math.max(view.length, 1);
  const barW = Math.max(1, Math.min(42, bw * 0.68));
  const y = (v: number) => T + ph * (1 - v / max);
  const cx = (i: number) => L + bw * i + bw / 2;
  const every = Math.max(1, Math.ceil(view.length / Math.max(2, Math.floor(pw / 64))));
  const line = view.map((p, i) => `${i ? "L" : "M"}${cx(i).toFixed(1)},${y(p.total).toFixed(1)}`).join("");
  const hp = hover != null ? view[hover] : null;
  const tipLeft = hover != null ? cx(hover) : 0;

  return (
    <div className="sc" ref={wrap}>
      <svg width={W} height={H} role="img" aria-label="Замовлення за періодом у розрізі статусів"
        onMouseLeave={() => setHover(null)}
        onMouseMove={(e) => {
          const r = (e.currentTarget as SVGSVGElement).getBoundingClientRect();
          const i = Math.floor((e.clientX - r.left - L) / bw);
          setHover(i >= 0 && i < view.length ? i : null);
        }}>
        {ticks.map((t) => (
          <g key={t}>
            <line x1={L} x2={W - R} y1={y(t)} y2={y(t)} className={t === 0 ? "sc-axis" : "sc-grid"} />
            <text x={L - 8} y={y(t) + 4} className="sc-tick" textAnchor="end">{t % 1 ? t.toFixed(1) : t}</text>
          </g>
        ))}
        {hover != null && <rect x={L + bw * hover} y={T} width={bw} height={ph} className="sc-hover" />}
        {view.map((p, i) => {
          let acc = 0;
          return (
            <g key={p.t}>
              {visible.map((s) => {
                const c = p.by_status[String(s.id)] ?? 0;
                if (!c) return null;
                const y0 = y(acc), y1 = y(acc + c);
                acc += c;
                return <rect key={s.id} x={cx(i) - barW / 2} y={y1} width={barW} height={Math.max(0.5, y0 - y1 - (barW > 6 ? 1 : 0))}
                  rx={barW > 8 ? 2 : 0} fill={s.color} opacity={hover == null || hover === i ? 0.92 : 0.55} />;
              })}
              {i % every === 0 && <text x={cx(i)} y={H - 8} className="sc-tick" textAnchor="middle">{axisLabel(p.t, group)}</text>}
            </g>
          );
        })}
        {showTotal && view.length > 1 && <path d={line} className="sc-line" />}
        {showTotal && view.map((p, i) => (view.length <= 62 || hover === i) && (
          <circle key={p.t} cx={cx(i)} cy={y(p.total)} r={hover === i ? 4.5 : view.length > 40 ? 2 : 3} className="sc-dot" />
        ))}
      </svg>
      {hp && (
        <div className={`sc-tip ${tipLeft > W * 0.62 ? "left" : ""}`} style={{ left: tipLeft }}>
          <div className="sc-tip-h">{fullLabel(hp.t, group)}</div>
          <div className="sc-tip-r all"><span className="sc-tip-line" /><span>Усі</span><b>{hp.total}</b></div>
          {statuses.filter((s) => hp.by_status[String(s.id)]).map((s) => (
            <div key={s.id} className={`sc-tip-r ${hidden.has(s.id) ? "off" : ""}`}>
              <span className="sc-tip-dot" style={{ background: s.color }} /><span>{s.name}</span><b>{hp.by_status[String(s.id)]}</b>
            </div>
          ))}
        </div>
      )}
      {n > 20 && <Navigator points={points} width={W} left={L} right={R} range={[a, b]} onRange={setRange} />}
    </div>
  );
}

// Повзунок періоду: мініграфік усіх відрізків і вікно, яке можна тягнути й розширювати.
function Navigator({ points, width, left, right, range, onRange }: {
  points: ChartPoint[]; width: number; left: number; right: number; range: [number, number]; onRange: (r: [number, number]) => void;
}) {
  const H = 46, n = points.length;
  const pw = width - left - right;
  const step = pw / Math.max(n - 1, 1);
  const max = Math.max(1, ...points.map((p) => p.total));
  const x = (i: number) => left + step * i;
  const area = `M${x(0)},${H - 4}` + points.map((p, i) => `L${x(i).toFixed(1)},${(H - 4 - (H - 10) * (p.total / max)).toFixed(1)}`).join("") + `L${x(n - 1)},${H - 4}Z`;
  const drag = useRef<{ mode: "move" | "a" | "b"; start: number; r: [number, number] } | null>(null);
  const idx = (clientX: number, el: Element) => {
    const r = el.getBoundingClientRect();
    return Math.max(0, Math.min(n - 1, Math.round((clientX - r.left - left) / step)));
  };
  const [a, b] = range;
  const full = a === 0 && b === n - 1;
  return (
    <div className="sc-nav">
      <svg width={width} height={H}
        onPointerDown={(e) => {
          const i = idx(e.clientX, e.currentTarget);
          const ax = x(a), bx = x(b), px = e.clientX - e.currentTarget.getBoundingClientRect().left;
          let mode: "move" | "a" | "b" = "move";
          if (Math.abs(px - ax) < 8) mode = "a";
          else if (Math.abs(px - bx) < 8) mode = "b";
          else if (i < a || i > b) { // клік поза вікном — перенести вікно туди
            const half = Math.floor((b - a) / 2);
            const na = Math.max(0, Math.min(n - 1 - (b - a), i - half));
            onRange([na, na + (b - a)]);
          }
          drag.current = { mode, start: i, r: [a, b] };
          e.currentTarget.setPointerCapture(e.pointerId);
        }}
        onPointerMove={(e) => {
          const d = drag.current;
          if (!d) return;
          const i = idx(e.clientX, e.currentTarget);
          if (d.mode === "a") onRange([Math.min(i, d.r[1] - 1), d.r[1]]);
          else if (d.mode === "b") onRange([d.r[0], Math.max(i, d.r[0] + 1)]);
          else {
            const w = d.r[1] - d.r[0];
            const na = Math.max(0, Math.min(n - 1 - w, d.r[0] + (i - d.start)));
            onRange([na, na + w]);
          }
        }}
        onPointerUp={() => { drag.current = null; }}>
        <path d={area} className="sc-nav-area" />
        <rect x={left} y={2} width={Math.max(0, x(a) - left)} height={H - 4} className="sc-nav-shade" />
        <rect x={x(b)} y={2} width={Math.max(0, width - right - x(b))} height={H - 4} className="sc-nav-shade" />
        <rect x={x(a)} y={2} width={Math.max(2, x(b) - x(a))} height={H - 4} className="sc-nav-win" />
        {[a, b].map((i, k) => <rect key={k} x={x(i) - 4} y={H / 2 - 9} width={8} height={18} rx={3} className="sc-nav-handle" />)}
      </svg>
      {!full && <button type="button" className="btn sm ghost sc-nav-reset" onClick={() => onRange([0, n - 1])}>Увесь період</button>}
    </div>
  );
}
