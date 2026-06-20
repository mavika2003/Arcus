"use client";

import dynamic from "next/dynamic";
import type { MonthlyTrend } from "@/lib/types";
import { formatCurrencyCompact } from "@/lib/currency";
import { basePlotLayout, useChartTheme } from "@/lib/theme";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface OverviewChartProps {
  data: MonthlyTrend[];
}

export default function OverviewChart({ data }: OverviewChartProps) {
  const ct = useChartTheme();

  if (data.length === 0) {
    return (
      <div className="flex h-[400px] items-center justify-center text-base text-text-muted">
        No monthly data yet — add sales and expense files for a month to see trends
      </div>
    );
  }

  const months = data.map((d) => d.Month);

  return (
    <Plot
      data={[
        {
          x: months,
          y: data.map((d) => d.net_sales),
          type: "bar",
          name: "Revenue",
          marker: {
            color: months.map(() => ct.accent),
            cornerradius: 8,
            line: { color: ct.accent2, width: 1 },
          },
          hovertemplate: "<b>Revenue</b><br>%{x}: %{y:,.0f} AED<extra></extra>",
        },
        {
          x: months,
          y: data.map((d) => d.total_expenses),
          type: "bar",
          name: "Total Cost",
          marker: {
            color: months.map(() => ct.barSecondary),
            cornerradius: 8,
            opacity: 0.85,
          },
          hovertemplate: "<b>Total Cost</b><br>%{x}: %{y:,.0f} AED<extra></extra>",
        },
        {
          x: months,
          y: data.map((d) => d.net_profit),
          type: "scatter",
          mode: "lines+markers+text",
          name: "Net Profit",
          text: data.map((d) => formatCurrencyCompact(d.net_profit)),
          textposition: "top center",
          textfont: { size: 11, color: ct.font },
          line: { color: ct.green, width: 3, shape: "spline" },
          marker: {
            size: 12,
            color: data.map((d) => (d.net_profit >= 0 ? ct.green : ct.red)),
            line: { color: "#fff", width: 2 },
            symbol: "circle",
          },
          hovertemplate: "<b>Net Profit</b><br>%{x}: %{y:,.0f} AED<extra></extra>",
        },
      ]}
      layout={{
        ...basePlotLayout(ct, 400),
        barmode: "group",
        bargap: 0.28,
        bargroupgap: 0.12,
        hovermode: "x unified",
        hoverlabel: {
          bgcolor: ct.plot,
          bordercolor: ct.grid,
          font: { size: 13, color: ct.font },
        },
        legend: {
          orientation: "h",
          y: 1.1,
          x: 0,
          font: { size: 13, color: ct.font },
          bgcolor: "transparent",
        },
      }}
      config={{ displayModeBar: false, responsive: true }}
      className="w-full"
    />
  );
}
