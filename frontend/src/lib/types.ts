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
  receipts?: ReceiptSummary[];
  receipt_count?: number;
  receipt_cash_outflow?: number;
}

export interface ReceiptLineItem {
  name: string;
  quantity?: number;
  unit_price?: number | null;
  amount?: number | null;
  barcode?: string | null;
}

export interface ReceiptSummary {
  id?: string | number;
  vendor_name?: string | null;
  transaction_date?: string | null;
  total_amount?: number | null;
  category?: string;
  pl_category?: string;
  currency?: string;
  payment_method?: string | null;
}

export interface ReceiptPreview {
  vendor_name?: string | null;
  transaction_date?: string | null;
  total_amount: number;
  currency?: string;
  tax_amount?: number | null;
  taxable_amount?: number | null;
  payment_method?: string | null;
  category?: string;
  pl_category?: string;
  category_confidence?: number;
  description?: string | null;
  line_items?: ReceiptLineItem[];
  warnings?: string[];
  raw_ocr_text?: string | null;
  source_filename?: string | null;
}

export interface ReceiptUploadResult {
  receipt: ReceiptPreview & {
    id?: string | number;
    persisted_to?: string;
    raw_text_preview?: string;
  };
  dashboard: DashboardData | null;
}
