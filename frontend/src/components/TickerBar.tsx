"use client";

export default function TickerBar() {
  const time = new Date().toUTCString().split(" ")[4];
  const items = [
    "Arcus — YTD Revenue Live",
    "Auto-Reconciliation: 99.8% Match",
    `System Clock: ${time} UTC`,
    "All Systems Operational",
    "P&L · Balance Sheet · Real-time",
  ];

  const ticker = [...items, ...items].join("   ◆   ");

  return (
    <div className="relative overflow-hidden border-b border-border bg-bg-secondary/80 py-2.5 backdrop-blur-sm">
      <div className="ticker-animate whitespace-nowrap text-sm font-medium tracking-wide text-text-muted">
        {ticker}
      </div>
    </div>
  );
}
