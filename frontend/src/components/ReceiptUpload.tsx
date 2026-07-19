"use client";

import { useState } from "react";
import { Camera, Loader2, Upload } from "lucide-react";
import { confirmReceipt, scanReceipt } from "@/lib/api";
import type { DashboardData, ReceiptPreview } from "@/lib/types";
import GlassCard, { SectionLabel, SectionTitle } from "@/components/GlassCard";
import ReceiptReviewModal from "@/components/ReceiptReviewModal";

interface ReceiptUploadProps {
  onDataLoaded?: (data: DashboardData) => void;
  onError?: (msg: string) => void;
  onViewPl?: () => void;
}

export default function ReceiptUpload({ onDataLoaded, onError, onViewPl }: ReceiptUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [scanning, setScanning] = useState(false);
  const [saving, setSaving] = useState(false);
  const [preview, setPreview] = useState<ReceiptPreview | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const handleScan = async () => {
    if (!file) {
      onError?.("Select a receipt photo (JPG/PNG) to upload.");
      return;
    }
    setScanning(true);
    setPreview(null);
    try {
      const res = await scanReceipt(file);
      setPreview(res.receipt);
      setModalOpen(true);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to scan receipt.";
      onError?.(msg);
    } finally {
      setScanning(false);
    }
  };

  const handleAccept = async (data: ReceiptPreview) => {
    setSaving(true);
    try {
      const res = await confirmReceipt(data);
      setModalOpen(false);
      setPreview(null);
      setFile(null);
      if (res.dashboard && onDataLoaded) {
        onDataLoaded(res.dashboard);
      }
      onViewPl?.();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to save receipt.";
      onError?.(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleCloseModal = () => {
    if (saving) return;
    setModalOpen(false);
  };

  return (
    <>
      <GlassCard className="p-6 md:col-span-2">
        <SectionLabel>Receipt OCR</SectionLabel>
        <SectionTitle>Scan Bills & Receipts</SectionTitle>
        <p className="mt-2 text-sm text-text-secondary">
          Upload a receipt photo. We extract vendor, date, total, and category — you review and
          edit in a confirmation step before it updates P&L and the balance sheet.
        </p>

        <div className="mt-5 grid gap-5 md:grid-cols-2">
          <label className="block">
            <span className="mb-2 block text-sm font-medium text-text-secondary">
              Receipt image (.jpg, .png, .webp)
            </span>
            <div className="flex items-center gap-3 rounded-xl border-2 border-dashed border-border px-4 py-6 transition-colors hover:border-accent/40">
              <Camera className="h-5 w-5 shrink-0 text-text-muted" />
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp,image/heic,.jpg,.jpeg,.png,.webp,.pdf"
                className="w-full text-sm text-text-secondary file:mr-3 file:cursor-pointer file:rounded-lg file:border-0 file:bg-accent file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
                onChange={(e) => {
                  setFile(e.target.files?.[0] ?? null);
                  setPreview(null);
                }}
              />
            </div>
            {file && (
              <p className="mt-2 truncate text-xs text-text-muted">{file.name}</p>
            )}
          </label>

          <div className="flex flex-col justify-end gap-3">
            <button
              onClick={handleScan}
              disabled={scanning || saving || !file}
              className="btn-primary w-full justify-center disabled:opacity-50"
            >
              {scanning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
              {scanning ? "Scanning with OCR…" : "Scan Receipt"}
            </button>
            <p className="text-xs text-text-muted">
              Human review required · edit fields in the popup before accepting
            </p>
          </div>
        </div>
      </GlassCard>

      <ReceiptReviewModal
        open={modalOpen}
        preview={preview}
        saving={saving}
        onClose={handleCloseModal}
        onAccept={handleAccept}
      />
    </>
  );
}
