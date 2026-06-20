"use client";

import { useState } from "react";
import { Upload, FileSpreadsheet, Loader2 } from "lucide-react";
import { uploadDashboard } from "@/lib/api";
import type { DashboardData } from "@/lib/types";
import GlassCard, { SectionLabel, SectionTitle } from "@/components/GlassCard";

interface UploadPanelProps {
  onDataLoaded: (data: DashboardData) => void;
  onError: (msg: string) => void;
}

export default function UploadPanel({ onDataLoaded, onError }: UploadPanelProps) {
  const [salesFile, setSalesFile] = useState<File | null>(null);
  const [plFile, setPlFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!salesFile && !plFile) {
      onError("Select at least one file to upload.");
      return;
    }
    setLoading(true);
    try {
      const data = await uploadDashboard(salesFile ?? undefined, plFile ?? undefined);
      onDataLoaded(data);
    } catch {
      onError("Failed to process files. Check format and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <GlassCard className="p-6">
      <SectionLabel>Data Ingestion</SectionLabel>
      <SectionTitle>Upload Files</SectionTitle>

      <div className="mt-5 space-y-5">
        <label className="block">
          <span className="mb-2 block text-sm font-medium text-text-secondary">
            Daily Sales (.numbers, .xlsx, .csv)
          </span>
          <div className="flex items-center gap-3 rounded-xl border-2 border-dashed border-border px-4 py-4 transition-colors hover:border-accent/40">
            <Upload className="h-5 w-5 text-text-muted" />
            <input
              type="file"
              accept=".numbers,.xlsx,.xls,.csv"
              className="text-sm text-text-secondary file:mr-3 file:cursor-pointer file:rounded-lg file:border-0 file:bg-accent file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
              onChange={(e) => setSalesFile(e.target.files?.[0] ?? null)}
            />
          </div>
        </label>

        <label className="block">
          <span className="mb-2 block text-sm font-medium text-text-secondary">
            P&L Account (.xlsx)
          </span>
          <div className="flex items-center gap-3 rounded-xl border-2 border-dashed border-border px-4 py-4 transition-colors hover:border-accent/40">
            <FileSpreadsheet className="h-5 w-5 text-text-muted" />
            <input
              type="file"
              accept=".xlsx,.xls"
              className="text-sm text-text-secondary file:mr-3 file:cursor-pointer file:rounded-lg file:border-0 file:bg-accent file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
              onChange={(e) => setPlFile(e.target.files?.[0] ?? null)}
            />
          </div>
        </label>

        <button
          onClick={handleUpload}
          disabled={loading}
          className="btn-primary w-full justify-center disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {loading ? "Processing…" : "Refresh Dashboard"}
        </button>
      </div>
    </GlassCard>
  );
}
