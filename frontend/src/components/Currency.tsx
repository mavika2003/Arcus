"use client";

import { AnimatedDirhamPrice, DirhamPrice } from "dirham/react";

interface CurrencyProps {
  amount: number;
  animated?: boolean;
  decimals?: number;
  compact?: boolean;
  className?: string;
  weight?: "regular" | "medium" | "semibold" | "bold";
}

export default function Currency({
  amount,
  animated = false,
  decimals,
  compact = false,
  className = "",
  weight = "semibold",
}: CurrencyProps) {
  const safeAmount = Number.isFinite(amount) ? amount : 0;
  const abs = Math.abs(safeAmount);
  const resolvedDecimals =
    decimals ?? (abs >= 1_000 ? 0 : 2);

  if (animated) {
    return (
      <AnimatedDirhamPrice
        amount={safeAmount}
        decimals={resolvedDecimals}
        notation={compact ? "compact" : "standard"}
        weight={weight}
        className={`dirham-amount ${className}`.trim()}
        duration={1200}
        easing="easeOut"
      />
    );
  }

  return (
    <DirhamPrice
      amount={safeAmount}
      decimals={resolvedDecimals}
      notation={compact ? "compact" : "standard"}
      weight={weight}
      className={`dirham-amount ${className}`.trim()}
    />
  );
}
