import type { YtdSummary } from "@/lib/types";

export function hasYtdSummary(
  ytd: Partial<YtdSummary> | null | undefined,
): ytd is YtdSummary {
  return (
    ytd != null &&
    typeof ytd.ytd_revenue === "number" &&
    Number.isFinite(ytd.ytd_revenue) &&
    typeof ytd.ytd_operating_margin === "number" &&
    Number.isFinite(ytd.ytd_operating_margin)
  );
}

export function formatMarginPct(value: number | null | undefined, digits = 1): string {
  const n = Number(value);
  return `${(Number.isFinite(n) ? n : 0).toFixed(digits)}%`;
}

export function safeNumber(value: number | null | undefined, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}
