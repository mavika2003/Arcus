"use client";

import dynamic from "next/dynamic";
import type { DailyTrend, MonthlyTrend } from "@/lib/types";
import { basePlotLayout, useChartTheme } from "@/lib/theme";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface TrendChartProps {
  daily: DailyTrend[];
  monthly: MonthlyTrend[];
  view: "daily" | "monthly";
}

export default function TrendChart({ daily, monthly, view }: TrendChartProps) {
  const ct = useChartTheme();

  if (view === "daily" && daily.length > 0) {
    return (
      <Plot
        data={[
          {
            x: daily.map((d) => d.date),
            y: daily.map((d) => d.sales),
            type: "scatter",
            mode: "lines",
            name: "Sales",
            line: { color: ct.accent, width: 2.5, shape: "spline" },
            fill: "tozeroy",
            fillcolor: `${ct.accent}18`,
            hovertemplate: "%{x}<br>%{y:,.0f} AED<extra></extra>",
          },
        ]}
        layout={{
          ...basePlotLayout(ct, 320),
          title: { text: "Daily Sales Trend", font: { size: 14, color: ct.font } },
          showlegend: false,
        }}
        config={{ displayModeBar: false, responsive: true }}
        className="w-full"
      />
    );
  }

  if (monthly.length > 0) {
    return (
      <Plot
        data={[
          {
            x: monthly.map((m) => m.Month),
            y: monthly.map((m) => m.net_sales),
            type: "bar",
            name: "Revenue",
            marker: { color: ct.accent, cornerradius: 5 },
            hovertemplate: "<b>Revenue</b><br>%{x}: %{y:,.0f} AED<extra></extra>",
          },
          {
            x: monthly.map((m) => m.Month),
            y: monthly.map((m) => m.total_expenses),
            type: "bar",
            name: "Expenses",
            marker: { color: ct.barSecondary, cornerradius: 5 },
            hovertemplate: "<b>Expenses</b><br>%{x}: %{y:,.0f} AED<extra></extra>",
          },
          {
            x: monthly.map((m) => m.Month),
            y: monthly.map((m) => m.net_profit),
            type: "scatter",
            mode: "lines+markers",
            name: "Net Profit",
            line: { color: ct.green, width: 2.5, shape: "spline" },
            marker: { size: 8 },
            hovertemplate: "<b>Net Profit</b><br>%{x}: %{y:,.0f} AED<extra></extra>",
          },
        ]}
        layout={{
          ...basePlotLayout(ct, 320),
          title: { text: "Monthly Sales vs Expenses", font: { size: 14, color: ct.font } },
          barmode: "group",
          legend: { font: { size: 12, color: ct.font } },
        }}
        config={{ displayModeBar: false, responsive: true }}
        className="w-full"
      />
    );
  }

  return (
    <div className="flex h-[320px] items-center justify-center text-base text-text-muted">
      No trend data available
    </div>
  );
}
