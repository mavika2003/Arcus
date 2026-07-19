/**
 * API calls use same-origin `/api/...`.
 * - JSON routes: next.config rewrites → Render
 * - Receipt OCR: Next.js route handlers (longer timeout, multipart-safe)
 *
 * Vercel env: API_URL = https://your-app.onrender.com
 */

function normalizeBackendUrl(raw: string | undefined | null): string | null {
  if (!raw?.trim()) return null;
  let url = raw.trim().replace(/\/$/, "");
  if (!/^https?:\/\//i.test(url)) url = `https://${url}`;
  return url;
}

function apiUrl(path: string): string {
  if (typeof window !== "undefined") return path;

  const base = normalizeBackendUrl(
    process.env.API_URL ??
      process.env.NEXT_PUBLIC_API_URL ??
      process.env.NEXT_PUBLIC_BACKEND_URL,
  );
  return base ? `${base}${path}` : path;
}

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const url = apiUrl(path);
  try {
    return await fetch(url, init);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Network error";
    throw new Error(`Failed to reach API (${url}): ${msg}`);
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
  if (res.status === 502 || res.status === 504 || res.status === 408) {
    return "OCR timed out — wait a moment for the server to wake up, then retry. If this keeps happening, redeploy the latest API build.";
  }
  return `${fallback} (HTTP ${res.status})`;
}

/** Wake Render free tier before a slow OCR request. */
async function wakeBackend(): Promise<void> {
  try {
    await apiFetch("/api/health", { cache: "no-store" });
  } catch {
    /* best-effort */
  }
}

export { formatCurrency, formatCurrencyTable, formatCurrencyCompact, chartCurrencyHover, DIRHAM_UNICODE } from "@/lib/currency";
export { compressReceiptImage } from "@/lib/compressImage";

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
  const maxMb = 12;
  if (file.size > maxMb * 1024 * 1024) {
    throw new Error(
      `Image is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Use a JPG under ${maxMb} MB.`,
    );
  }

  const { compressReceiptImage } = await import("@/lib/compressImage");
  const compressed = await compressReceiptImage(file);

  await wakeBackend();

  const form = new FormData();
  form.append("file", compressed);

  const startRes = await apiFetch("/api/upload-receipt", {
    method: "POST",
    body: form,
  });
  if (!startRes.ok) {
    throw new Error(await readErrorDetail(startRes, "Failed to start receipt scan"));
  }

  const started = await startRes.json();
  const jobId = started.job_id as string | undefined;

  // Backward compat: sync response from older backend
  if (!jobId && started.receipt) {
    return { receipt: started.receipt, dashboard: started.dashboard ?? null };
  }
  if (!jobId) {
    throw new Error("Invalid scan response from server");
  }

  // Poll until OCR completes (Render OCR can take 30–90s on free tier)
  const maxAttempts = 45;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    await new Promise((r) => setTimeout(r, 2000));

    const pollRes = await apiFetch(`/api/upload-receipt/${jobId}`, {
      cache: "no-store",
    });
    if (pollRes.status === 404) {
      throw new Error("Scan job expired — please try again.");
    }
    if (!pollRes.ok) {
      throw new Error(await readErrorDetail(pollRes, "Failed to scan receipt"));
    }

    const data = await pollRes.json();
    if (data.status === "complete" && data.receipt) {
      return { receipt: data.receipt, dashboard: data.dashboard ?? null };
    }
    if (data.status === "failed") {
      throw new Error(data.detail || "OCR failed");
    }
  }

  throw new Error("OCR is taking too long — please try again in a moment.");
}

/** @deprecated use scanReceipt — kept for compatibility */
export const uploadReceipt = scanReceipt;

export async function confirmReceipt(receipt: import("@/lib/types").ReceiptPreview) {
  const res = await apiFetch("/api/receipts/confirm", {
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
  const res = await apiFetch(`/api/receipts/latest${q}`, {
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
  return apiUrl(`/api/export/${type}`);
}
