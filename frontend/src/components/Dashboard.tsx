"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Download, RefreshCw, Sparkles, Zap } from "lucide-react";
import Header, { type DashboardTab } from "@/components/Header";
import TickerBar from "@/components/TickerBar";
import MetricCard from "@/components/MetricCard";
import PLTable from "@/components/PLTable";
import PLFlowDiagram from "@/components/PLFlowDiagram";
import AlertsPanel from "@/components/AlertsPanel";
import TrendChart from "@/components/TrendChart";
import ExpenseChart from "@/components/ExpenseChart";
import SalesChart from "@/components/SalesChart";
import OverviewChart from "@/components/OverviewChart";
import ProfitMarginChart, { MonthSummaryCards } from "@/components/ProfitMarginChart";
import BalanceSheetView from "@/components/BalanceSheetView";
import UploadPanel from "@/components/UploadPanel";
import Categorizer from "@/components/Categorizer";
import GlassCard, { SectionLabel, SectionTitle } from "@/components/GlassCard";
import { exportUrl, fetchDashboard } from "@/lib/api";
import Currency from "@/components/Currency";
import type { DashboardData } from "@/lib/types";

type Tab = DashboardTab;

const TABS: [Tab, string][] = [
  ["overview", "Overview"],
  ["pl", "P&L Statement"],
  ["balance", "Balance Sheet"],
  ["tools", "Tools"],
];

export default function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("overview");
  const [trendView, setTrendView] = useState<"daily" | "monthly">("monthly");
  const [expenseVariant, setExpenseVariant] = useState<"pie" | "bar">("bar");
  const mainRef = useRef<HTMLElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchDashboard();
      setData(result);
    } catch {
      setError("Could not connect to API. Start the backend with: uvicorn backend.main:app --reload");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const navigate = useCallback((next: Tab) => {
    setTab(next);
    mainRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  if (loading && !data) {
    return (
      <div className="relative flex min-h-screen items-center justify-center">
        <div className="page-bg" />
        <div className="relative z-10 text-center">
          <div className="mx-auto mb-6 h-12 w-12 animate-spin rounded-full border-[3px] border-accent/30 border-t-accent" />
          <p className="text-base font-medium text-text-secondary">Loading financial data…</p>
          <p className="mt-1 text-sm text-text-muted">Computing P&L & balance sheet</p>
        </div>
      </div>
    );
  }

  const ytd = data?.ytd_summary;

  return (
    <div className="relative min-h-screen">
      <div className="page-bg" aria-hidden />

      <div className="relative z-10">
        <Header
          activeTab={tab}
          onTabChange={navigate}
          onUploadClick={() => navigate("tools")}
        />
        <TickerBar />

        {error && (
          <div className="border-b border-red/30 bg-red/10 px-6 py-4 text-center">
            <p className="text-sm text-red">{error}</p>
            <button
              onClick={load}
              className="mt-2 inline-flex items-center gap-2 text-sm font-medium text-accent hover:underline"
            >
              <RefreshCw className="h-4 w-4" /> Retry connection
            </button>
          </div>
        )}

        <main ref={mainRef} className="mx-auto max-w-[1440px] px-5 py-8 md:px-8 md:py-10">
          <section className="mb-10 animate-fade-up">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-accent" />
              <SectionLabel>Financial Control Center</SectionLabel>
            </div>
            <h1 className="mt-3 text-4xl font-bold leading-[1.1] tracking-tight md:text-6xl lg:text-7xl">
              <span className="gradient-text">Arcus.</span>{" "}
              <span className="text-text">One dashboard.</span>
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-relaxed text-text-secondary md:text-lg">
              P&L and balance sheet computed automatically from your monthly sales and expense data.
              Drop new files into Sales/ and Expenses/ — watch the numbers update in real time.
            </p>
          </section>

          {ytd && (
            <section className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard
                label="YTD Revenue"
                value={ytd.ytd_revenue}
                sub="Net sales after discounts"
                trend="up"
                delay={0}
                onClick={() => navigate("overview")}
              />
              <MetricCard
                label="Total Cost"
                value={ytd.ytd_total_expenses}
                sub="COGS + operating expenses"
                delay={80}
                onClick={() => navigate("pl")}
              />
              <MetricCard
                label="Net Profit"
                value={ytd.ytd_net_profit}
                accent
                sub="Revenue − all costs"
                trend={ytd.ytd_net_profit >= 0 ? "up" : "down"}
                delay={160}
                onClick={() => navigate("balance")}
              />
              <MetricCard
                label="Operating Margin"
                value={`${ytd.ytd_operating_margin.toFixed(1)}%`}
                sub="Net profit / revenue"
                delay={240}
                onClick={() => navigate("overview")}
              />
            </section>
          )}

          <div className="tab-nav mb-8 flex">
            {TABS.map(([key, label]) => (
              <button
                key={key}
                onClick={() => navigate(key)}
                className={`tab-btn ${tab === key ? "active" : ""}`}
              >
                {label}
              </button>
            ))}
          </div>

          <div key={tab} className="animate-fade-up">
            {tab === "overview" && data && ytd && (
              <div className="space-y-6">
                <PLFlowDiagram ytd={ytd} onNavigate={navigate} />

                <GlassCard className="p-6 md:p-8" glow delay={50}>
                  <SectionLabel>Monthly Overview</SectionLabel>
                  <SectionTitle>Revenue · Total Cost · Net Profit</SectionTitle>
                  <div className="mt-6">
                    <OverviewChart data={data.monthly_trends} />
                  </div>
                </GlassCard>

                <MonthSummaryCards data={data.monthly_trends} />

                <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
                  <div className="space-y-6">
                    <GlassCard className="p-6 md:p-8" delay={100}>
                      <ProfitMarginChart data={data.monthly_trends} />
                    </GlassCard>

                    <GlassCard className="p-6 md:p-8" delay={150}>
                      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <SectionLabel>Performance</SectionLabel>
                          <SectionTitle>Trend Analysis</SectionTitle>
                        </div>
                        <div className="flex gap-1 rounded-lg bg-bg-secondary p-1">
                          {(["daily", "monthly"] as const).map((v) => (
                            <button
                              key={v}
                              onClick={() => setTrendView(v)}
                              className={`chip-btn ${trendView === v ? "active" : ""}`}
                            >
                              {v.charAt(0).toUpperCase() + v.slice(1)}
                            </button>
                          ))}
                        </div>
                      </div>
                      <TrendChart
                        daily={data.daily_trends}
                        monthly={data.monthly_trends}
                        view={trendView}
                      />
                    </GlassCard>

                    <div className="grid gap-6 md:grid-cols-2">
                      <GlassCard className="p-6" delay={200}>
                        <div className="mb-4 flex gap-1 rounded-lg bg-bg-secondary p-1">
                          {(["bar", "pie"] as const).map((v) => (
                            <button
                              key={v}
                              onClick={() => setExpenseVariant(v)}
                              className={`chip-btn ${expenseVariant === v ? "active" : ""}`}
                            >
                              {v.charAt(0).toUpperCase() + v.slice(1)}
                            </button>
                          ))}
                        </div>
                        <ExpenseChart data={data.expense_breakdown} variant={expenseVariant} />
                      </GlassCard>
                      <GlassCard className="p-6" delay={250}>
                        <SalesChart data={data.payment_distribution} />
                      </GlassCard>
                    </div>
                  </div>

                  <aside className="space-y-6">
                    <AlertsPanel alerts={data.alerts} />

                    <GlassCard className="p-6" delay={300}>
                      <SectionLabel>Data Processed</SectionLabel>
                      <div className="mt-3 font-mono text-4xl font-bold text-text">
                        {data.transaction_count.toLocaleString()}
                      </div>
                      <p className="mt-1 text-sm text-text-secondary">Daily sales transactions</p>
                      <div className="my-4 h-px bg-gradient-to-r from-transparent via-accent/40 to-transparent" />
                      <p className="text-sm font-semibold text-accent">
                        {data.months.length} month{data.months.length !== 1 ? "s" : ""} loaded
                      </p>
                    </GlassCard>

                    <GlassCard className="p-6" glow delay={350}>
                      <SectionLabel>YTD Net Position</SectionLabel>
                      <div className={`mt-3 text-4xl font-bold ${ytd.ytd_net_profit >= 0 ? "text-green" : "text-red"}`}>
                        {ytd.ytd_net_profit >= 0 ? "+" : ""}
                        <Currency amount={ytd.ytd_net_profit} weight="bold" />
                      </div>
                    </GlassCard>
                  </aside>
                </div>
              </div>
            )}

            {tab === "pl" && data && (
              <div className="space-y-6">
                {ytd && <PLFlowDiagram ytd={ytd} onNavigate={navigate} />}
                <PLTable rows={data.pl_display_rows} months={data.months} />
              </div>
            )}

            {tab === "balance" && data && <BalanceSheetView data={data.balance_sheet} />}

            {tab === "tools" && (
              <div className="grid gap-6 md:grid-cols-2">
                <UploadPanel
                  onDataLoaded={(d) => { setData(d); setError(null); navigate("overview"); }}
                  onError={setError}
                />
                <Categorizer />

                <GlassCard className="p-6 md:col-span-2" delay={100}>
                  <SectionLabel>Export</SectionLabel>
                  <SectionTitle>Download Reports</SectionTitle>
                  <p className="mt-2 mb-6 text-base text-text-secondary">
                    Export clean, automated data for your tax accountant.
                  </p>
                  <div className="flex flex-wrap gap-4">
                    <a href={exportUrl("excel")} className="btn-primary">
                      <Download className="h-4 w-4" />
                      Export Excel
                    </a>
                    <a
                      href={exportUrl("pdf")}
                      className="inline-flex items-center gap-2 rounded-xl border border-border px-5 py-2.5 text-sm font-semibold text-text-secondary transition-all hover:border-accent hover:text-accent"
                    >
                      <Download className="h-4 w-4" />
                      Export PDF
                    </a>
                  </div>
                </GlassCard>
              </div>
            )}
          </div>

          {data?.warnings && data.warnings.length > 0 && (
            <div className="mt-6 space-y-2">
              {data.warnings.map((w, i) => (
                <p key={i} className="text-sm text-amber">⚠ {w}</p>
              ))}
            </div>
          )}
        </main>

        <footer className="mt-12 border-t border-border">
          <div className="mx-auto flex max-w-[1440px] flex-wrap items-center justify-between gap-4 px-5 py-6 md:px-8">
            <div className="flex flex-wrap items-center gap-5 text-sm text-text-muted">
              <span className="flex items-center gap-2">
                <Zap className="h-4 w-4 text-accent" />
                {data?.transaction_count ?? 0} transactions
              </span>
              <span>{data?.months.length ?? 0} months</span>
              <span className="flex items-center gap-1.5 font-medium text-green">
                <span className="h-2 w-2 animate-pulse-dot rounded-full bg-green" />
                Live
              </span>
            </div>
            <div className="text-sm font-medium text-text-muted">
              Arcus Financial Dashboard
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
