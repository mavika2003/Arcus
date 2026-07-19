function resolveApiBase(): string {
  const fromEnv =
    process.env.NEXT_PUBLIC_API_URL ??
    process.env.NEXT_PUBLIC_BACKEND_URL;

  if (fromEnv) return fromEnv.replace(/\/$/, "");

  // Local dev — backend runs separately (uvicorn on :8000)
  return "http://localhost:8000";
}

const API_BASE = resolveApiBase();

export { formatCurrency, formatCurrencyTable, formatCurrencyCompact, chartCurrencyHover, DIRHAM_UNICODE } from "@/lib/currency";

export async function fetchDashboard() {
  const res = await fetch(`${API_BASE}/api/dashboard`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load dashboard data");
  return res.json();
}

export async function uploadDashboard(salesFile?: File, plFile?: File) {
  const form = new FormData();
  if (salesFile) form.append("sales_file", salesFile);
  if (plFile) form.append("pl_file", plFile);

  const res = await fetch(`${API_BASE}/api/dashboard/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Failed to process uploaded files");
  return res.json();
}

export async function categorizeExpense(description: string) {
  const res = await fetch(`${API_BASE}/api/categorize`, {
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

  const res = await fetch(`${API_BASE}/api/upload-receipt`, {
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
  const res = await fetch(`${API_BASE}/api/receipts/confirm`, {
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
  const res = await fetch(`${API_BASE}/api/receipts/latest${q}`, {
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
  const res = await fetch(`${API_BASE}/api/receipts`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load receipts");
  return res.json();
}

export function exportUrl(type: "excel" | "pdf"): string {
  return `${API_BASE}/api/export/${type}`;
}
