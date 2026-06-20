export interface YtdSummary {
  ytd_revenue: number;
  ytd_gross_profit: number;
  ytd_total_expenses: number;
  ytd_net_profit: number;
  ytd_operating_margin: number;
  ytd_cogs: number;
  ytd_operating_expenses: number;
}

export interface PLDisplayRow {
  type?: string;
  label?: string;
  ytd?: number;
  Jan?: number;
  Feb?: number;
  [key: string]: string | number | undefined;
}

export interface Alert {
  severity: string;
  category: string;
  message: string;
  pct_change?: number;
}

export interface ExpenseItem {
  category: string;
  amount: number;
}

export interface PaymentItem {
  mode: string;
  amount: number;
}

export interface DailyTrend {
  date: string;
  sales: number;
  tax: number;
}

export interface MonthlyTrend {
  Month: string;
  net_sales: number;
  total_expenses: number;
  net_profit: number;
}

export interface BalanceSheetItem {
  item: string;
  amount: number | null;
}

export interface BalanceSheet {
  total_assets: number;
  total_liabilities: number;
  shareholders_equity: number;
  retained_earnings: number;
  total_equity: number;
  assets: BalanceSheetItem[];
  liabilities: BalanceSheetItem[];
}

export interface DashboardData {
  company_name: string;
  ytd_summary: YtdSummary;
  pl_monthly: Record<string, number | string>[];
  pl_display_rows: PLDisplayRow[];
  months: string[];
  expense_breakdown: ExpenseItem[];
  payment_distribution: PaymentItem[];
  daily_trends: DailyTrend[];
  monthly_trends: MonthlyTrend[];
  alerts: Alert[];
  balance_sheet: BalanceSheet;
  warnings: string[];
  transaction_count: number;
}
