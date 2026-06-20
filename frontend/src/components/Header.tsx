"use client";

import { ArrowUpRight, Cog } from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";

export type DashboardTab = "overview" | "pl" | "balance" | "tools";

const NAV_ITEMS: { label: string; tab: DashboardTab }[] = [
  { label: "Overview", tab: "overview" },
  { label: "Reports", tab: "pl" },
  { label: "Analytics", tab: "balance" },
  { label: "Settings", tab: "tools" },
];

interface HeaderProps {
  activeTab: DashboardTab;
  onTabChange: (tab: DashboardTab) => void;
  onUploadClick?: () => void;
}

export default function Header({ activeTab, onTabChange, onUploadClick }: HeaderProps) {
  return (
    <header className="header-glass">
      <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-4 px-5 py-4 md:px-8">
        <button
          onClick={() => onTabChange("overview")}
          className="flex items-center gap-3 text-left transition-opacity hover:opacity-80"
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent/10">
            <Cog className="h-5 w-5 text-accent" strokeWidth={2} />
          </div>
          <div>
            <span className="text-lg font-bold tracking-[0.15em] text-text">ARCUS</span>
            <div className="flex items-center gap-1.5">
              <span className="h-2 w-2 animate-pulse-dot rounded-full bg-green" />
              <span className="text-xs font-medium text-green">Live · Financial OS</span>
            </div>
          </div>
        </button>

        <nav className="hidden items-center gap-1 lg:flex">
          {NAV_ITEMS.map(({ label, tab }) => (
            <button
              key={tab}
              onClick={() => onTabChange(tab)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-all ${
                activeTab === tab
                  ? "bg-accent/10 text-accent"
                  : "text-text-secondary hover:bg-bg-secondary hover:text-text"
              }`}
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="flex items-center gap-3">
          <ThemeToggle variant="header" />
          <button onClick={onUploadClick} className="btn-primary text-sm">
            Upload Data
            <ArrowUpRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
