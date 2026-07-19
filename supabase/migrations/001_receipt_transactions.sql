-- Run this in Supabase → SQL Editor if Accept fails with
-- "Could not find the table 'public.receipt_transactions'"

create table if not exists receipt_transactions (
  id bigserial primary key,
  company_id uuid not null references companies(id) on delete cascade,
  transaction_date date not null,
  vendor_name text,
  total_amount numeric not null default 0,
  currency text not null default 'AED',
  tax_amount numeric,
  taxable_amount numeric,
  payment_method text,
  category text not null default 'Sundry Expenses',
  pl_category text not null default 'Sundry Expenses',
  description text,
  line_items jsonb not null default '[]'::jsonb,
  image_url text,
  raw_ocr_text text,
  category_confidence numeric,
  created_at timestamptz not null default now()
);

create index if not exists idx_receipt_company_date
  on receipt_transactions(company_id, transaction_date);

alter table receipt_transactions enable row level security;
