"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus, Trash2, X } from "lucide-react";
import type { ReceiptLineItem, ReceiptPreview } from "@/lib/types";
import { formatCurrency } from "@/lib/currency";

export const PL_CATEGORIES = [
  "COGS",
  "Salaries",
  "Rent",
  "Utilities",
  "Office Expenditure",
  "Staff Expenses",
  "Sundry Expenses",
  "Taxes",
] as const;

const PAYMENT_METHODS = ["VISA", "MASTERCARD", "CASH", "MAGNATI", "EFT", "CARD"] as const;

const emptyLine = (): ReceiptLineItem => ({
  name: "",
  quantity: 1,
  unit_price: null,
  amount: null,
  barcode: null,
});

interface ReceiptReviewModalProps {
  open: boolean;
  preview: ReceiptPreview | null;
  saving?: boolean;
  onClose: () => void;
  onAccept: (data: ReceiptPreview) => void;
}

export default function ReceiptReviewModal({
  open,
  preview,
  saving = false,
  onClose,
  onAccept,
}: ReceiptReviewModalProps) {
  const [form, setForm] = useState<ReceiptPreview | null>(null);

  useEffect(() => {
    if (preview) {
      setForm({
        ...preview,
        line_items: preview.line_items?.length ? [...preview.line_items] : [],
      });
    }
  }, [preview]);

  const lineItems = form?.line_items ?? [];

  const itemsSubtotal = useMemo(
    () => lineItems.reduce((sum, li) => sum + (Number(li.amount) || 0), 0),
    [lineItems],
  );

  if (!open || !form) return null;

  const set = <K extends keyof ReceiptPreview>(key: K, value: ReceiptPreview[K]) => {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
  };

  const setLineItem = (index: number, patch: Partial<ReceiptLineItem>) => {
    setForm((prev) => {
      if (!prev) return prev;
      const items = [...(prev.line_items ?? [])];
      const current = { ...items[index], ...patch };
      if (patch.unit_price !== undefined || patch.quantity !== undefined) {
        const price = Number(current.unit_price) || 0;
        const qty = Number(current.quantity) || 1;
        if (price > 0) current.amount = Math.round(price * qty * 100) / 100;
      }
      items[index] = current;
      return { ...prev, line_items: items };
    });
  };

  const addLineItem = () => {
    setForm((prev) =>
      prev ? { ...prev, line_items: [...(prev.line_items ?? []), emptyLine()] } : prev,
    );
  };

  const removeLineItem = (index: number) => {
    setForm((prev) => {
      if (!prev) return prev;
      const items = [...(prev.line_items ?? [])];
      items.splice(index, 1);
      return { ...prev, line_items: items };
    });
  };

  const inputClass =
    "mt-1 w-full rounded-xl border border-border bg-bg-secondary px-3 py-2.5 text-sm text-text focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20";

  const cellInput =
    "w-full rounded-lg border border-border bg-bg-secondary px-2 py-1.5 text-sm text-text focus:border-accent focus:outline-none";

  const totalDiff =
    form.total_amount && itemsSubtotal > 0
      ? Math.abs(form.total_amount - itemsSubtotal)
      : 0;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="receipt-review-title"
    >
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={saving ? undefined : onClose}
        aria-label="Close"
      />

      <div className="relative z-10 flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-border bg-bg shadow-2xl">
        <div className="flex items-start justify-between border-b border-border px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-accent">Review receipt</p>
            <h2 id="receipt-review-title" className="mt-1 text-lg font-semibold text-text">
              Confirm extracted data
            </h2>
            <p className="mt-1 text-sm text-text-secondary">
              Edit header fields and each product line before accepting.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="rounded-lg p-2 text-text-muted transition-colors hover:bg-bg-secondary hover:text-text disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-5">
          {form.warnings && form.warnings.length > 0 && (
            <ul className="mb-4 space-y-1 rounded-xl border border-amber/30 bg-amber/10 px-3 py-2">
              {form.warnings.map((w, i) => (
                <li key={i} className="text-xs text-amber">⚠ {w}</li>
              ))}
            </ul>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="sm:col-span-2 block">
              <span className="text-xs font-medium text-text-muted">Vendor</span>
              <input
                type="text"
                value={form.vendor_name ?? ""}
                onChange={(e) => set("vendor_name", e.target.value)}
                className={inputClass}
              />
            </label>

            <label className="block">
              <span className="text-xs font-medium text-text-muted">Date</span>
              <input
                type="date"
                value={form.transaction_date?.slice(0, 10) ?? ""}
                onChange={(e) => set("transaction_date", e.target.value)}
                className={inputClass}
              />
            </label>

            <label className="block">
              <span className="text-xs font-medium text-text-muted">Bill total (AED)</span>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.total_amount ?? ""}
                onChange={(e) => set("total_amount", parseFloat(e.target.value) || 0)}
                className={inputClass}
              />
            </label>

            <label className="block">
              <span className="text-xs font-medium text-text-muted">Tax amount</span>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.tax_amount ?? ""}
                onChange={(e) =>
                  set("tax_amount", e.target.value ? parseFloat(e.target.value) : null)
                }
                className={inputClass}
              />
            </label>

            <label className="block">
              <span className="text-xs font-medium text-text-muted">Payment method</span>
              <select
                value={form.payment_method ?? ""}
                onChange={(e) => set("payment_method", e.target.value || null)}
                className={inputClass}
              >
                <option value="">—</option>
                {PAYMENT_METHODS.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-xs font-medium text-text-muted">P&L category</span>
              <select
                value={form.pl_category ?? "Sundry Expenses"}
                onChange={(e) => {
                  set("pl_category", e.target.value);
                  set("category", e.target.value);
                }}
                className={inputClass}
              >
                {PL_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </label>
          </div>

          <div className="mt-6">
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-text">Products</h3>
                <p className="text-xs text-text-muted">Qty × unit price = line amount</p>
              </div>
              <button
                type="button"
                onClick={addLineItem}
                className="inline-flex items-center gap-1.5 rounded-lg border border-border px-3 py-1.5 text-xs font-semibold text-text-secondary hover:border-accent hover:text-accent"
              >
                <Plus className="h-3.5 w-3.5" />
                Add row
              </button>
            </div>

            <div className="overflow-x-auto rounded-xl border border-border">
              <table className="w-full min-w-[640px] text-left text-sm">
                <thead className="border-b border-border bg-bg-secondary/80 text-xs uppercase tracking-wide text-text-muted">
                  <tr>
                    <th className="px-3 py-2.5 font-semibold">Product</th>
                    <th className="w-16 px-2 py-2.5 font-semibold">Qty</th>
                    <th className="w-24 px-2 py-2.5 font-semibold">Unit</th>
                    <th className="w-24 px-2 py-2.5 font-semibold">Amount</th>
                    <th className="w-10 px-2 py-2.5" />
                  </tr>
                </thead>
                <tbody>
                  {lineItems.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-3 py-6 text-center text-text-muted">
                        No products detected — click &quot;Add row&quot; to enter manually.
                      </td>
                    </tr>
                  ) : (
                    lineItems.map((item, i) => (
                      <tr key={i} className="border-b border-border/60 last:border-0">
                        <td className="px-3 py-2">
                          <input
                            type="text"
                            value={item.name}
                            onChange={(e) => setLineItem(i, { name: e.target.value })}
                            className={cellInput}
                            placeholder="Product name"
                          />
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            min="0"
                            step="0.001"
                            value={item.quantity ?? 1}
                            onChange={(e) =>
                              setLineItem(i, { quantity: parseFloat(e.target.value) || 1 })
                            }
                            className={cellInput}
                          />
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={item.unit_price ?? ""}
                            onChange={(e) =>
                              setLineItem(i, {
                                unit_price: e.target.value ? parseFloat(e.target.value) : null,
                              })
                            }
                            className={cellInput}
                          />
                        </td>
                        <td className="px-2 py-2">
                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={item.amount ?? ""}
                            onChange={(e) =>
                              setLineItem(i, {
                                amount: e.target.value ? parseFloat(e.target.value) : null,
                              })
                            }
                            className={cellInput}
                          />
                        </td>
                        <td className="px-2 py-2">
                          <button
                            type="button"
                            onClick={() => removeLineItem(i)}
                            className="rounded p-1.5 text-text-muted hover:bg-red/10 hover:text-red"
                            aria-label="Remove row"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
                {lineItems.length > 0 && (
                  <tfoot className="border-t border-border bg-bg-secondary/50 text-sm">
                    <tr>
                      <td colSpan={3} className="px-3 py-2.5 text-right font-medium text-text-secondary">
                        Products subtotal
                      </td>
                      <td className="px-2 py-2.5 font-semibold tabular-nums text-text">
                        {formatCurrency(itemsSubtotal)}
                      </td>
                      <td />
                    </tr>
                    {totalDiff > 0.05 && (
                      <tr>
                        <td colSpan={5} className="px-3 pb-2.5 text-xs text-amber">
                          Subtotal differs from bill total by {formatCurrency(totalDiff)}
                        </td>
                      </tr>
                    )}
                  </tfoot>
                )}
              </table>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-border px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            disabled={saving}
            className="rounded-xl border border-border px-4 py-2.5 text-sm font-semibold text-text-secondary transition-colors hover:border-accent hover:text-accent disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={saving || !form.total_amount}
            onClick={() => onAccept({ ...form, line_items: lineItems })}
            className="btn-primary min-w-[120px] justify-center disabled:opacity-50"
          >
            {saving ? "Saving…" : "Accept"}
          </button>
        </div>
      </div>
    </div>
  );
}
