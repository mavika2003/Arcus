"use client";

import dynamic from "next/dynamic";
import type { MonthlyTrend } from "@/lib/types";
import Currency from "@/components/Currency";
import { basePlotLayout, useChartTheme } from "@/lib/theme";
import GlassCard from "@/components/GlassCard";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface ProfitMarginChartProps {
  data: MonthlyTrend[];
}

export default function ProfitMarginChart({ data }: ProfitMarginChartProps) {
  const ct = useChartTheme();

  if (data.length === 0) return null;

  const margins = data.map((d) =>
    d.net_sales > 0 ? (d.net_profit / d.net_sales) * 100 : 0
  );

  return (
    <Plot
      data={[
        {
          x: data.map((d) => d.Month),
          y: margins,
          type: "bar",
          marker: {
            color: margins.map((m) => (m >= 0 ? ct.green : ct.red)),
            cornerradius: 6,
          },
          hovertemplate: "%{x}<br>Margin: %{y:.1f}%<extra></extra>",
          text: margins.map((m) => `${m.toFixed(1)}%`),
          textposition: "outside",
          textfont: { size: 12, color: ct.font },
        },
      ]}
      layout={{
        ...basePlotLayout(ct, 260),
        title: { text: "Operating Margin by Month", font: { size: 14, color: ct.font } },
        yaxis: { ...basePlotLayout(ct).yaxis, ticksuffix: "%" },
        showlegend: false,
      }}
      config={{ displayModeBar: false, responsive: true }}
      className="w-full"
    />
  );
}

export function MonthSummaryCards({ data }: ProfitMarginChartProps) {
  if (data.length === 0) return null;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {data.map((m, i) => {
        const margin = m.net_sales > 0 ? (m.net_profit / m.net_sales) * 100 : 0;
        const positive = m.net_profit >= 0;
        return (
          <GlassCard key={m.Month} className="p-5" delay={i * 80}>
            <div className="section-label">{m.Month} 2026</div>
            <div className="mt-2 text-2xl font-bold text-text md:text-3xl">
              <Currency amount={m.net_sales} weight="bold" />
            </div>
            <div className="text-sm text-text-muted">Revenue</div>
            <div className="mt-4 space-y-2 border-t border-border pt-4">
              <div className="flex justify-between text-sm">
                <span className="text-text-secondary">Total Cost</span>
                <span className="font-medium"><Currency amount={m.total_expenses} /></span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-text-secondary">Net Profit</span>
                <span className={`font-bold ${positive ? "text-green" : "text-red"}`}>
                  <Currency amount={m.net_profit} weight="semibold" />
                </span>
              </div>
            </div>
            <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-border">
              <div
                className={`h-full rounded-full transition-all duration-700 ${positive ? "bg-green" : "bg-red"}`}
                style={{ width: `${Math.min(Math.abs(margin), 100)}%` }}
              />
            </div>
            <div className="mt-1.5 text-xs text-text-muted">
              {margin.toFixed(1)}% margin
            </div>
          </GlassCard>
        );
      })}
    </div>
  );
}
