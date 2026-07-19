/**
 * Most API calls use same-origin `/api/...` (Vercel → Render rewrite).
 * Receipt OCR goes directly to Render — large uploads + slow Tesseract time out
 * through Vercel's proxy.
 *
 * Vercel env vars:
 *   API_URL              = https://your-app.onrender.com  (server rewrite)
 *   NEXT_PUBLIC_API_URL  = https://your-app.onrender.com  (browser OCR)
 */

function normalizeBackendUrl(raw: string | undefined | null): string | null {
  if (!raw?.trim()) return null;
  let url = raw.trim().replace(/\/$/, "");
  if (!/^https?:\/\//i.test(url)) url = `https://${url}`;
  return url;
}

function proxyApiUrl(path: string): string {
  if (typeof window !== "undefined") return path;
  const base = normalizeBackendUrl(
    process.env.API_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      process.env.NEXT_PUBLIC_BACKEND_URL,
  );
  return base ? `${base}${path}` : path;
}

/** Direct Render URL for long-running OCR uploads (browser only). */
function directBackendUrl(path: string): string {
  const base = normalizeBackendUrl(
    process.env.NEXT_PUBLIC_API_URL ??
      process.env.NEXT_PUBLIC_BACKEND_URL ??
      process.env.API_URL,
  );
  if (base) return `${base}${path}`;
  // Local / fallback: same-origin proxy
  return proxyApiUrl(path);
}

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = proxyApiUrl(path);
  try {
    return await fetch(url, init);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Network error";
    throw new Error(`Failed to reach API (${url}): ${msg}`);
  }
}

async function directFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = directBackendUrl(path);
  try {
    return await fetch(url, init);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Network error";
    const hint =
      typeof window !== "undefined" && !process.env.NEXT_PUBLIC_API_URL
        ? " Set NEXT_PUBLIC_API_URL=https://your-app.onrender.com on Vercel and redeploy."
        : "";
    throw new Error(`Failed to reach backend (${url}): ${msg}.${hint}`);
  }
}

async function readErrorDetail(res: Response, fallback: string): Promise<string> {
  try {
    const body = await res.json();
    const detail = body.detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return detail.map((d) => d.msg || JSON.stringify(d)).join("; ") || fallback;
    }
  } catch {
    /* ignore */
  }
  return `${fallback} (HTTP ${res.status})`;
}

export { formatCurrency, formatCurrencyTable, formatCurrencyCompact, chartCurrencyHover, DIRHAM_UNICODE } from "@/lib/currency";

export async function fetchDashboard() {
  const res = await apiFetch("/api/dashboard", { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load dashboard data");
  return res.json();
}

export async function uploadDashboard(salesFile?: File, plFile?: File) {
  const form = new FormData();
  if (salesFile) form.append("sales_file", salesFile);
  if (plFile) form.append("pl_file", plFile);

  const res = await apiFetch("/api/dashboard/upload", {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Failed to process uploaded files");
  return res.json();
}

export async function categorizeExpense(description: string) {
  const res = await apiFetch("/api/categorize", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ description }),
  });
  if (!res.ok) throw new Error("Categorization failed");
  return res.json();
}

export async function scanReceipt(file: File) {
  // Phone photos can be large — warn early
  const maxMb = 12;
  if (file.size > maxMb * 1024 * 1024) {
    throw new Error(
      `Image is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Use a JPG under ${maxMb} MB.`,
    );
  }

  const form = new FormData();
  form.append("file", file);

  // Direct to Render — OCR can take 30–90s; Vercel proxy times out
  const res = await directFetch("/api/upload-receipt", {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    throw new Error(await readErrorDetail(res, "Failed to scan receipt"));
  }
  return res.json();
}

/** @deprecated use scanReceipt — kept for compatibility */
export const uploadReceipt = scanReceipt;

export async function confirmReceipt(receipt: import("@/lib/types").ReceiptPreview) {
  const res = await directFetch("/api/receipts/confirm", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(receipt),
  });
  if (!res.ok) {
    throw new Error(await readErrorDetail(res, "Failed to save receipt"));
  }
  return res.json();
}

export async function deleteLatestReceipt(month?: string) {
  const q = month ? `?month=${encodeURIComponent(month)}` : "";
  const res = await directFetch(`/api/receipts/latest${q}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    throw new Error(await readErrorDetail(res, "Failed to delete receipt"));
  }
  return res.json();
}

export async function fetchReceipts() {
  const res = await apiFetch("/api/receipts", { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load receipts");
  return res.json();
}

export function exportUrl(type: "excel" | "pdf"): string {
  return proxyApiUrl(`/api/export/${type}`);
}
