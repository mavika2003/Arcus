"use client";

import { TrendingDown, TrendingUp } from "lucide-react";
import Currency from "@/components/Currency";
import GlassCard from "@/components/GlassCard";

interface MetricCardProps {
  label: string;
  value: number | string;
  sub?: string;
  accent?: boolean;
  trend?: "up" | "down" | null;
  delay?: number;
  onClick?: () => void;
}

export default function MetricCard({ label, value, sub, accent, trend, delay = 0, onClick }: MetricCardProps) {
  const isNumber = typeof value === "number";
  const display = isNumber ? null : value;
  const isPositive = isNumber && value >= 0;

  return (
    <GlassCard
      className={`metric-card p-6 md:p-7 ${onClick ? "cursor-pointer" : ""}`}
      glow={accent}
      delay={delay}
      onClick={onClick}
    >
      <div className="mb-4 flex items-start justify-between">
        <span className="text-sm font-semibold uppercase tracking-wide text-text-muted">
          {label}
        </span>
        {trend && (
          <span className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${
            trend === "up" ? "bg-green/10 text-green" : "bg-red/10 text-red"
          }`}>
            {trend === "up" ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
          </span>
        )}
      </div>

      <div
        className={`text-3xl font-bold tracking-tight md:text-4xl lg:text-[2.75rem] lg:leading-none ${
          accent
            ? isNumber && !isPositive
              ? "text-red"
              : "gradient-text"
            : "text-text"
        }`}
      >
        {isNumber ? (
          <Currency
            amount={value}
            animated
            compact={Math.abs(value) >= 1_000_000}
            weight="bold"
          />
        ) : (
          display
        )}
      </div>

      {sub && (
        <p className="mt-3 text-sm leading-relaxed text-text-secondary">{sub}</p>
      )}
    </GlassCard>
  );
}
