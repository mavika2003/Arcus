"use client";

import { formatCurrency } from "@/lib/api";
import Currency from "@/components/Currency";
import type { BalanceSheet } from "@/lib/types";
import dynamic from "next/dynamic";
import GlassCard, { SectionLabel, SectionTitle } from "@/components/GlassCard";
import { useChartTheme } from "@/lib/theme";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

function SummaryTile({ label, value, accent, positive }: {
  label: string;
  value: number;
  accent?: boolean;
  positive?: boolean;
}) {
  return (
    <GlassCard className="p-5 md:p-6" glow={accent}>
      <div className="text-sm font-semibold uppercase tracking-wide text-text-muted">{label}</div>
      <div className={`mt-2 text-2xl font-bold md:text-3xl ${
        accent ? "gradient-text" :
        positive === false ? "text-red" :
        positive === true ? "text-green" : "text-text"
      }`}>
        <Currency amount={value} weight="bold" compact={Math.abs(value) >= 1_000_000} />
      </div>
    </GlassCard>
  );
}

interface EquitySlice {
  label: string;
  value: number;
  color: string;
}

function EquityCompositionChart({
  shareholdersEquity,
  retainedEarnings,
  totalEquity,
}: {
  shareholdersEquity: number;
  retainedEarnings: number;
  totalEquity: number;
}) {
  const ct = useChartTheme();

  const slices: EquitySlice[] = [
    { label: "Shareholders Equity", value: shareholdersEquity, color: ct.accent },
    { label: "Retained Earnings", value: retainedEarnings, color: ct.green },
  ].filter((s) => s.value !== 0);

  if (slices.length === 0) return null;

  const total = slices.reduce((sum, s) => sum + Math.abs(s.value), 0);
  const pulls = slices.map((s) => (Math.abs(s.value) / total < 0.08 ? 0.06 : 0));

  return (
    <div className="grid items-center gap-8 lg:grid-cols-[1fr_280px]">
      <div className="relative mx-auto w-full max-w-[420px]">
        <Plot
          data={[{
            labels: slices.map((s) => s.label),
            values: slices.map((s) => Math.abs(s.value)),
            type: "pie",
            hole: 0.62,
            pull: pulls,
            marker: {
              colors: slices.map((s) => s.color),
              line: { color: "rgba(255,255,255,0.9)", width: 3 },
            },
            textinfo: "none",
            hovertemplate: "<b>%{label}</b><br>%{value:,.0f} AED<br>%{percent}<extra></extra>",
            sort: false,
            direction: "clockwise",
          }]}
          layout={{
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            font: { family: "Inter, system-ui, sans-serif", color: ct.font, size: 13 },
            height: 340,
            width: 420,
            margin: { l: 10, r: 10, t: 10, b: 10 },
            showlegend: false,
            annotations: [
              {
                text: formatCurrency(totalEquity),
                showarrow: false,
                font: { size: 20, color: ct.font, family: "JetBrains Mono, monospace" },
                x: 0.5,
                y: 0.52,
              },
              {
                text: "Total Equity",
                showarrow: false,
                font: { size: 11, color: ct.font },
                x: 0.5,
                y: 0.42,
              },
            ],
          }}
          config={{ displayModeBar: false, responsive: true }}
          className="w-full"
          useResizeHandler
        />
      </div>

      <div className="space-y-3">
        {slices.map((slice) => {
          const pct = total > 0 ? (Math.abs(slice.value) / total) * 100 : 0;
          return (
            <div
              key={slice.label}
              className="rounded-xl border border-border bg-bg-secondary/40 p-4 transition-colors hover:border-border-light"
            >
              <div className="flex items-center gap-3">
                <span
                  className="h-3 w-3 shrink-0 rounded-full"
                  style={{ backgroundColor: slice.color }}
                />
                <span className="text-sm font-medium text-text-secondary">{slice.label}</span>
              </div>
              <div className="mt-2 flex items-baseline justify-between gap-4">
                <span className="text-xl font-bold tabular-nums text-text">
                  <Currency amount={slice.value} weight="semibold" />
                </span>
                <span className="font-mono text-sm font-semibold tabular-nums text-text-muted">
                  {pct.toFixed(1)}%
                </span>
              </div>
              <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-border">
                <div
                  className="h-full rounded-full transition-all duration-700"
                  style={{ width: `${pct}%`, backgroundColor: slice.color }}
                />
              </div>
            </div>
          );
        })}

        <div className="rounded-xl border border-accent/20 bg-accent/5 p-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-text-muted">
            Total Equity
          </div>
          <div className="mt-1 text-2xl font-bold gradient-text">
            <Currency amount={totalEquity} weight="bold" />
          </div>
        </div>
      </div>
    </div>
  );
}

export default function BalanceSheetView({ data }: { data: BalanceSheet }) {
  const hasEquity = data.shareholders_equity !== 0 || data.retained_earnings !== 0;

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryTile label="Shareholders Equity" value={data.shareholders_equity} />
        <SummaryTile label="Retained Earnings" value={data.retained_earnings} positive={data.retained_earnings >= 0} />
        <SummaryTile label="Total Equity" value={data.total_equity} accent />
        <SummaryTile label="Total Liabilities" value={data.total_liabilities} />
      </div>

      <div className="grid gap-5 md:grid-cols-2">
        <GlassCard className="p-6">
          <SectionLabel>Balance Sheet</SectionLabel>
          <SectionTitle>Assets</SectionTitle>
          <div className="mt-5 space-y-3">
            {data.assets.map((item, i) => (
              <div key={i} className="flex justify-between text-base">
                <span className="text-text-secondary">{item.item}</span>
                <span className="font-medium tabular-nums">
                  {item.amount != null ? <Currency amount={item.amount} /> : "—"}
                </span>
              </div>
            ))}
            {data.assets.every((a) => a.amount == null) && (
              <p className="text-sm italic text-text-muted">Asset values not yet recorded</p>
            )}
          </div>
          <div className="mt-5 flex justify-between border-t border-border pt-4 text-base font-bold">
            <span>Total Assets</span>
            <span className="gradient-text"><Currency amount={data.total_assets} weight="bold" /></span>
          </div>
        </GlassCard>

        <GlassCard className="p-6">
          <SectionLabel>Liabilities & Equity</SectionLabel>
          <SectionTitle>Obligations & Equity</SectionTitle>
          <div className="mt-5 space-y-3">
            {data.liabilities.map((item, i) => (
              <div key={i} className="flex justify-between text-base">
                <span className="text-text-secondary">{item.item}</span>
                <span className="font-medium tabular-nums">
                  {item.amount != null ? <Currency amount={item.amount} /> : "—"}
                </span>
              </div>
            ))}
            <div className="flex justify-between text-base">
              <span className="text-text-secondary">Retained Earnings (YTD P&L)</span>
              <span className={data.retained_earnings >= 0 ? "text-green" : "text-red"}>
                <Currency amount={data.retained_earnings} weight="semibold" />
              </span>
            </div>
          </div>
          <div className="mt-5 flex justify-between border-t border-border pt-4 text-base font-bold">
            <span>Total Equity</span>
            <span className="gradient-text"><Currency amount={data.total_equity} weight="bold" /></span>
          </div>
        </GlassCard>
      </div>

      {hasEquity && (
        <GlassCard className="p-6 md:p-8">
          <SectionLabel>Equity Composition</SectionLabel>
          <SectionTitle>How total equity is built</SectionTitle>
          <p className="mt-1 mb-6 text-sm text-text-secondary">
            Shareholders equity from the balance sheet plus retained earnings from YTD net profit
          </p>
          <EquityCompositionChart
            shareholdersEquity={data.shareholders_equity}
            retainedEarnings={data.retained_earnings}
            totalEquity={data.total_equity}
          />
        </GlassCard>
      )}
    </div>
  );
}
