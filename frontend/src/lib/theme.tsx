"use client";

import { createContext, useContext, useEffect, useState } from "react";

export type Theme = "dark" | "light";

interface ThemeContextValue {
  theme: Theme;
  toggle: () => void;
  setTheme: (t: Theme) => void;
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: "dark",
  toggle: () => {},
  setTheme: () => {},
});

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("arcus-theme") as Theme | null;
    if (saved === "light" || saved === "dark") setThemeState(saved);
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("arcus-theme", theme);
  }, [theme, mounted]);

  const setTheme = (t: Theme) => setThemeState(t);
  const toggle = () => setThemeState((t) => (t === "dark" ? "light" : "dark"));

  return (
    <ThemeContext.Provider value={{ theme, toggle, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}

export interface ChartTheme {
  paper: string;
  plot: string;
  font: string;
  grid: string;
  accent: string;
  accent2: string;
  green: string;
  red: string;
  barSecondary: string;
  colors: string[];
}

const DARK_CHART: ChartTheme = {
  paper: "rgba(10,10,10,0)",
  plot: "rgba(17,17,17,0.5)",
  font: "#888888",
  grid: "#1f1f1f",
  accent: "#ff5722",
  accent2: "#ff8a65",
  green: "#22c55e",
  red: "#ef4444",
  barSecondary: "#2a2a2a",
  colors: ["#ff5722", "#ff8a65", "#22c55e", "#60a5fa", "#a78bfa", "#fbbf24"],
};

const LIGHT_CHART: ChartTheme = {
  paper: "rgba(255,255,255,0)",
  plot: "rgba(248,249,252,0.8)",
  font: "#64748b",
  grid: "#e2e8f0",
  accent: "#ea580c",
  accent2: "#fb923c",
  green: "#16a34a",
  red: "#dc2626",
  barSecondary: "#cbd5e1",
  colors: ["#ea580c", "#fb923c", "#16a34a", "#2563eb", "#7c3aed", "#ca8a04"],
};

export function useChartTheme(): ChartTheme {
  const { theme } = useTheme();
  return theme === "light" ? LIGHT_CHART : DARK_CHART;
}

export function basePlotLayout(ct: ChartTheme, height = 300) {
  return {
    paper_bgcolor: ct.paper,
    plot_bgcolor: ct.plot,
    font: { family: "Inter, system-ui, sans-serif", color: ct.font, size: 13 },
    margin: { l: 56, r: 24, t: 48, b: 48 },
    height,
    xaxis: { gridcolor: ct.grid, linecolor: ct.grid, zerolinecolor: ct.grid, tickfont: { size: 12 } },
    yaxis: { gridcolor: ct.grid, linecolor: ct.grid, zerolinecolor: ct.grid, tickfont: { size: 12 }, tickprefix: "AED ", tickformat: ",.0f" },
  };
}
