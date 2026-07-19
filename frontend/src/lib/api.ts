/**
 * API base URL for fetch calls.
 * Production uses same-origin `/api/...` proxied to Render via next.config rewrites.
 * Set API_URL on Vercel (or NEXT_PUBLIC_API_URL for direct cross-origin calls).
 */
function resolveApiBase(): string {
  const direct =
    process.env.NEXT_PUBLIC_API_URL ??
    process.env.NEXT_PUBLIC_BACKEND_URL;

  if (direct) return direct.replace(/\/$/, "");

  // Same-origin: Vercel/next dev rewrites forward /api → backend
  if (typeof window !== "undefined") return "";

  // Server components / SSR fallback during build
  return (
    process.env.API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
}

function apiUrl(path: string): string {
  const base = resolveApiBase();
  return base ? `${base}${path}` : path;
}

export { formatCurrency, formatCurrencyTable, formatCurrencyCompact, chartCurrencyHover, DIRHAM_UNICODE } from "@/lib/currency";

export async function fetchDashboard() {
  const res = await fetch(apiUrl("/api/dashboard"), { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load dashboard data");
  return res.json();
}

export async function uploadDashboard(salesFile?: File, plFile?: File) {
  const form = new FormData();
  if (salesFile) form.append("sales_file", salesFile);
  if (plFile) form.append("pl_file", plFile);

  const res = await fetch(apiUrl("/api/dashboard/upload"), {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Failed to process uploaded files");
  return res.json();
}

export async function categorizeExpense(description: string) {
  const res = await fetch(apiUrl("/api/categorize"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description }),
  });
  if (!res.ok) throw new Error("Categorization failed");
  return res.json();
}

export async function scanReceipt(file: File) {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(apiUrl("/api/upload-receipt"), {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    let detail = "Failed to scan receipt";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

/** @deprecated use scanReceipt — kept for compatibility */
export const uploadReceipt = scanReceipt;

export async function confirmReceipt(receipt: import("@/lib/types").ReceiptPreview) {
  const res = await fetch(apiUrl("/api/receipts/confirm"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(receipt),
  });
  if (!res.ok) {
    let detail = "Failed to save receipt";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function deleteLatestReceipt(month?: string) {
  const q = month ? `?month=${encodeURIComponent(month)}` : "";
  const res = await fetch(apiUrl(`/api/receipts/latest${q}`), {
    method: "DELETE",
  });
  if (!res.ok) {
    let detail = "Failed to delete receipt";
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function fetchReceipts() {
  const res = await fetch(apiUrl("/api/receipts"), { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load receipts");
  return res.json();
}

export function exportUrl(type: "excel" | "pdf"): string {
  return apiUrl(`/api/export/${type}`);
}
