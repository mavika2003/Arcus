"use client";

import Currency from "@/components/Currency";
import type { PLDisplayRow } from "@/lib/types";
import GlassCard, { SectionLabel, SectionTitle } from "@/components/GlassCard";

interface PLTableProps {
  rows: PLDisplayRow[];
  months: string[];
}

function StatusBadge({ label }: { label: string }) {
  const lower = label.toLowerCase();
  let cls = "bg-accent/15 text-accent";
  if (lower.includes("profit") || lower.includes("revenue")) cls = "bg-green/15 text-green";
  if (lower.includes("expense") || lower.includes("cogs") || lower.includes("cost"))
    cls = "bg-amber/15 text-amber";

  const status =
    lower.includes("profit") ? "Reconciled" :
    lower.includes("revenue") ? "Live" :
    lower.includes("expense") ? "Pending" : "Reconciled";

  return (
    <span className={`inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${cls}`}>
      {status}
    </span>
  );
}

function AmountCell({ value, bold }: { value: number; bold?: boolean }) {
  const negative = value < 0;
  return (
    <td className={`pl-amount-cell ${bold ? "font-bold text-text" : "text-text-secondary"}`}>
      <span className={`inline-flex justify-end tabular-nums ${negative ? "text-red" : ""}`}>
        <Currency amount={value} decimals={0} weight={bold ? "bold" : "regular"} />
      </span>
    </td>
  );
}

export default function PLTable({ rows, months }: PLTableProps) {
  const displayMonths = months.length > 0 ? months : ["Jan", "Feb"];
  const colCount = 2 + displayMonths.length; // account + ytd + months + status

  return (
    <GlassCard className="overflow-hidden">
      <div className="border-b border-border px-6 py-5">
        <SectionLabel>General Ledger</SectionLabel>
        <div className="flex items-center gap-3">
          <SectionTitle>Live Chart of Accounts</SectionTitle>
          <span className="flex items-center gap-1.5 rounded-full bg-green/10 px-2.5 py-1 text-xs font-semibold text-green">
            <span className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-green" />
            Live
          </span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="pl-table w-full min-w-[720px] border-collapse">
          <thead>
            <tr className="border-b border-border bg-bg-secondary/50">
              <th className="pl-label-cell text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                Account
              </th>
              <th className="pl-amount-cell text-xs font-semibold uppercase tracking-wider text-text-muted">
                YTD
              </th>
              {displayMonths.map((m) => (
                <th key={m} className="pl-amount-cell text-xs font-semibold uppercase tracking-wider text-text-muted">
                  {m}
                </th>
              ))}
              <th className="pl-status-cell text-left text-xs font-semibold uppercase tracking-wider text-text-muted">
                Status
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => {
              if (row.type === "section") {
                return (
                  <tr key={i} className="border-b border-border bg-accent/5">
                    <td
                      colSpan={colCount}
                      className="px-6 py-3 text-sm font-bold uppercase tracking-wider text-accent"
                    >
                      {row.label}
                    </td>
                  </tr>
                );
              }

              const label = row.label ?? "";
              const isTotal =
                /total|net profit|gross profit/i.test(label) && !label.startsWith("-");

              return (
                <tr
                  key={i}
                  className={`border-b border-border transition-colors hover:bg-bg-secondary/30 ${
                    isTotal ? "bg-bg-secondary/20" : ""
                  }`}
                >
                  <td className={`pl-label-cell ${isTotal ? "font-bold text-text" : "text-text-secondary"}`}>
                    {label}
                  </td>
                  <AmountCell value={Number(row.ytd ?? 0)} bold={isTotal} />
                  {displayMonths.map((m) => (
                    <AmountCell key={m} value={Number(row[m] ?? 0)} bold={isTotal} />
                  ))}
                  <td className="pl-status-cell">
                    <StatusBadge label={label} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </GlassCard>
  );
}
