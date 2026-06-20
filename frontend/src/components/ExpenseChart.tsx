"use client";

import dynamic from "next/dynamic";
import type { ExpenseItem } from "@/lib/types";
import { basePlotLayout, useChartTheme } from "@/lib/theme";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface ExpenseChartProps {
  data: ExpenseItem[];
  variant: "pie" | "bar";
}

export default function ExpenseChart({ data, variant }: ExpenseChartProps) {
  const ct = useChartTheme();

  if (data.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-base text-text-muted">
        No expense data
      </div>
    );
  }

  const layout = {
    ...basePlotLayout(ct, 300),
    title: { text: "Expense Breakdown", font: { size: 14, color: ct.font } },
    showlegend: variant === "pie" ? false : undefined,
    margin: { l: variant === "bar" ? 120 : 20, r: 20, t: 40, b: 20 },
  };

  if (variant === "pie") {
    return (
      <Plot
        data={[{
          labels: data.map((d) => d.category),
          values: data.map((d) => d.amount),
          type: "pie",
          hole: 0.55,
          marker: { colors: ct.colors },
          textinfo: "label+percent",
          textfont: { size: 11 },
          hovertemplate: "%{label}<br>%{value:,.0f} AED<extra></extra>",
        }]}
        layout={layout}
        config={{ displayModeBar: false, responsive: true }}
        className="w-full"
      />
    );
  }

  const sorted = [...data].sort((a, b) => a.amount - b.amount);
  return (
    <Plot
      data={[{
        x: sorted.map((d) => d.amount),
        y: sorted.map((d) => d.category),
        type: "bar",
        orientation: "h",
        marker: {
          color: sorted.map((_, i) =>
            i === sorted.length - 1 ? ct.accent : ct.barSecondary
          ),
          cornerradius: 4,
        },
        hovertemplate: "%{y}<br>%{x:,.0f} AED<extra></extra>",
      }]}
      layout={layout}
      config={{ displayModeBar: false, responsive: true }}
      className="w-full"
    />
  );
}
