import { DIRHAM_UNICODE, formatDirham } from "dirham";

type FormatOpts = {
  decimals?: number;
  compact?: boolean;
  /** Plain strings / Plotly use AED; React components use SVG via Currency */
  useCode?: boolean;
};

function formatSigned(amount: number, opts: FormatOpts = {}): string {
  const sign = amount < 0 ? "-" : "";
  const abs = Math.abs(amount);
  const formatted = formatDirham(abs, {
    locale: "en-AE",
    decimals: opts.decimals ?? 2,
    notation: opts.compact ? "compact" : "standard",
    useCode: opts.useCode ?? true,
  });
  return `${sign}${formatted}`;
}

/** Plain-text currency — AED prefix (charts, Plotly, table strings) */
export function formatCurrency(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1_000_000) return formatSigned(value, { compact: true, decimals: 2, useCode: true });
  if (abs >= 1_000) return formatSigned(value, { decimals: 0, useCode: true });
  return formatSigned(value, { decimals: 2, useCode: true });
}

/** Fixed-width table formatting — whole dirhams, aligned columns */
export function formatCurrencyTable(value: number): string {
  return formatSigned(value, { decimals: 0, useCode: true });
}

/** Compact label for charts e.g. AED 77.3k */
export function formatCurrencyCompact(value: number): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 1_000) {
    return `${sign}AED ${(abs / 1000).toFixed(1)}k`;
  }
  return formatSigned(value, { decimals: 0, useCode: true });
}

/** Plotly / tooltip hover strings */
export function chartCurrencyHover(value: number): string {
  return formatSigned(value, { decimals: 0, useCode: true });
}

export { DIRHAM_UNICODE };
