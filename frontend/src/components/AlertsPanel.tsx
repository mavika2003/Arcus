"use client";

import type { Alert } from "@/lib/types";
import GlassCard, { SectionLabel, SectionTitle } from "@/components/GlassCard";

export default function AlertsPanel({ alerts }: { alerts: Alert[] }) {
  return (
    <GlassCard className="overflow-hidden" delay={200}>
      <div className="border-b border-border px-6 py-5">
        <SectionLabel>Anomaly Detection</SectionLabel>
        <SectionTitle>Live Alert Feed</SectionTitle>
      </div>

      <div className="max-h-[360px] space-y-3 overflow-y-auto p-5">
        {alerts.length === 0 ? (
          <div className="rounded-xl border border-border bg-bg-secondary/50 p-4">
            <div className="text-xs font-semibold uppercase tracking-wider text-green">All Clear</div>
            <p className="mt-1 text-sm leading-relaxed text-text-secondary">
              No anomalies detected. All expenses within normal range.
            </p>
          </div>
        ) : (
          alerts.slice(0, 8).map((alert, i) => {
            const severity = alert.severity.toLowerCase();
            const styles =
              severity === "critical"
                ? "border-red/40 bg-red/5"
                : severity === "warning"
                ? "border-amber/40 bg-amber/5"
                : "border-border bg-bg-secondary/30";

            const labelColor =
              severity === "critical" ? "text-red" :
              severity === "warning" ? "text-amber" : "text-text-muted";

            return (
              <div
                key={i}
                className={`rounded-xl border-l-4 p-4 transition-transform duration-200 hover:translate-x-1 ${styles}`}
                style={{
                  borderLeftColor: severity === "critical" ? "var(--red)" :
                    severity === "warning" ? "var(--amber)" : "var(--text-muted)",
                }}
              >
                <div className={`text-xs font-bold uppercase tracking-wider ${labelColor}`}>
                  {alert.severity}
                </div>
                <p className="mt-1.5 text-sm leading-relaxed text-text-secondary">
                  {alert.message}
                </p>
              </div>
            );
          })
        )}
      </div>
    </GlassCard>
  );
}
