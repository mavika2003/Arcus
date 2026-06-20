"use client";

import { useState } from "react";
import { categorizeExpense } from "@/lib/api";
import GlassCard, { SectionLabel, SectionTitle } from "@/components/GlassCard";

export default function Categorizer() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<{
    category: string;
    confidence: number;
    method: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  const handleCategorize = async () => {
    if (!input.trim()) return;
    setLoading(true);
    try {
      const res = await categorizeExpense(input);
      setResult(res);
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <GlassCard className="p-6">
      <SectionLabel>Auto-Classify</SectionLabel>
      <SectionTitle>AI Expense Categorizer</SectionTitle>

      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleCategorize()}
        placeholder='e.g. "DEWA electricity bill"'
        className="mt-5 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-base text-text placeholder:text-text-muted focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
      />

      <button
        onClick={handleCategorize}
        disabled={loading}
        className="mt-4 w-full rounded-xl border border-border py-3 text-sm font-semibold text-text-secondary transition-all hover:border-accent hover:text-accent disabled:opacity-50"
      >
        {loading ? "Analyzing…" : "Categorize"}
      </button>

      {result && (
        <div className="mt-5 rounded-xl border border-accent/20 bg-accent/5 p-5">
          <div className="text-xs font-semibold uppercase tracking-wider text-text-muted">Suggested Category</div>
          <div className="mt-1 text-2xl font-bold gradient-text">{result.category}</div>
          <div className="mt-2 text-sm text-text-secondary">
            Confidence: {(result.confidence * 100).toFixed(0)}% · {result.method}
          </div>
        </div>
      )}
    </GlassCard>
  );
}
