"use client";

import dynamic from "next/dynamic";
import type { PaymentItem } from "@/lib/types";
import { basePlotLayout, useChartTheme } from "@/lib/theme";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

export default function SalesChart({ data }: { data: PaymentItem[] }) {
  const ct = useChartTheme();

  if (data.length === 0) {
    return (
      <div className="flex h-[300px] items-center justify-center text-base text-text-muted">
        No payment data
      </div>
    );
  }

  return (
    <Plot
      data={[{
        x: data.map((d) => d.mode),
        y: data.map((d) => d.amount),
        type: "bar",
        marker: { color: ct.colors.slice(0, data.length), cornerradius: 6 },
        hovertemplate: "%{x}<br>%{y:,.0f} AED<extra></extra>",
      }]}
      layout={{
        ...basePlotLayout(ct, 300),
        title: { text: "Sales by Payment Mode", font: { size: 14, color: ct.font } },
        showlegend: false,
      }}
      config={{ displayModeBar: false, responsive: true }}
      className="w-full"
    />
  );
}
