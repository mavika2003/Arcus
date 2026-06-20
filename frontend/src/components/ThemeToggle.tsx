"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "@/lib/theme";

export default function ThemeToggle({ variant = "header" }: { variant?: "header" | "floating" }) {
  const { theme, toggle } = useTheme();
  const isLight = theme === "light";

  if (variant === "floating") {
    return (
      <button
        onClick={toggle}
        aria-label={isLight ? "Switch to dark mode" : "Switch to light mode"}
        className="theme-toggle-float group fixed right-5 top-24 z-50 flex items-center gap-2.5 rounded-full border border-border bg-surface/90 px-4 py-2.5 shadow-lg backdrop-blur-xl transition-all duration-300 hover:scale-105 hover:border-accent/40 hover:shadow-accent/10"
      >
        <span className="text-sm font-medium text-text-secondary">
          {isLight ? "Dark" : "Light"}
        </span>
        <div className="relative h-6 w-11 rounded-full bg-border transition-colors duration-300 group-hover:bg-border-light">
          <div
            className={`absolute top-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-accent text-white shadow-md transition-all duration-300 ${
              isLight ? "left-0.5" : "left-[22px]"
            }`}
          >
            {isLight ? <Sun className="h-3 w-3" /> : <Moon className="h-3 w-3" />}
          </div>
        </div>
      </button>
    );
  }

  return (
    <button
      onClick={toggle}
      aria-label={isLight ? "Switch to dark mode" : "Switch to light mode"}
      className="group flex items-center gap-2 rounded-xl border border-border bg-surface-elevated px-3 py-2 transition-all duration-300 hover:border-accent/30 hover:shadow-md"
    >
      <div className="relative h-6 w-11 rounded-full bg-border transition-colors duration-300">
        <div
          className={`absolute top-0.5 flex h-5 w-5 items-center justify-center rounded-full transition-all duration-300 ${
            isLight
              ? "left-0.5 bg-amber text-white"
              : "left-[22px] bg-accent text-white"
          }`}
        >
          {isLight ? <Sun className="h-3 w-3" /> : <Moon className="h-3 w-3" />}
        </div>
      </div>
      <span className="hidden text-sm font-medium text-text-secondary sm:inline">
        {isLight ? "Light" : "Dark"}
      </span>
    </button>
  );
}
