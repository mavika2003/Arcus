-- Arcus financial dashboard schema + seed data
-- Run in Supabase → SQL Editor → New query → Run

create extension if not exists "pgcrypto";

create table if not exists companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  fiscal_year int not null default 2026,
  created_at timestamptz not null default now()
);

create table if not exists sales_transactions (
  id bigserial primary key,
  company_id uuid not null references companies(id) on delete cascade,
  sale_date date not null,
  month text not null,
  restaurant text,
  keeta numeric default 0,
  careem numeric default 0,
  smile numeric default 0,
  talabat numeric default 0,
  noon numeric default 0,
  discount numeric default 0,
  gross_sale numeric default 0,
  net_sale_bt numeric default 0,
  tax numeric default 0,
  net_sale_at numeric default 0,
  cash numeric default 0,
  master_card numeric default 0,
  visa_card numeric default 0,
  zomato_paid numeric default 0,
  pay_later numeric default 0,
  online_pay numeric default 0,
  created_at timestamptz not null default now()
);

create table if not exists recurring_expenses (
  id bigserial primary key,
  company_id uuid not null references companies(id) on delete cascade,
  category text not null,
  month text not null,
  amount numeric not null default 0,
  fiscal_year int not null default 2026
);

create table if not exists monthly_cogs (
  id bigserial primary key,
  company_id uuid not null references companies(id) on delete cascade,
  month text not null,
  cogs numeric not null default 0,
  fiscal_year int not null default 2026,
  unique (company_id, month, fiscal_year)
);

create table if not exists balance_sheet_items (
  id bigserial primary key,
  company_id uuid not null references companies(id) on delete cascade,
  side text not null check (side in ('asset', 'liability', 'equity')),
  item text not null,
  amount numeric,
  as_of_date date not null default '2025-12-31'
);

-- OCR-extracted bills / supermarket receipts (feeds P&L + balance sheet cash)
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

create index if not exists idx_sales_company_date on sales_transactions(company_id, sale_date);
create index if not exists idx_recurring_company_month on recurring_expenses(company_id, month);
create index if not exists idx_receipt_company_date on receipt_transactions(company_id, transaction_date);

alter table companies enable row level security;
alter table sales_transactions enable row level security;
alter table recurring_expenses enable row level security;
alter table monthly_cogs enable row level security;
alter table balance_sheet_items enable row level security;
alter table receipt_transactions enable row level security;


do $$
declare
  cid uuid;
begin
  select id into cid from companies where name = 'Arcus' limit 1;
  if cid is null then
    insert into companies (name, fiscal_year) values ('Arcus', 2026) returning id into cid;
  end if;

  delete from sales_transactions where company_id = cid;
  delete from recurring_expenses where company_id = cid;
  delete from monthly_cogs where company_id = cid;
  delete from balance_sheet_items where company_id = cid;

  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-01', 'Feb', 1787.0, 0.0, 0.0, 0.0, 37.0, 257.0, 0.0, 2081.0, 2081.0, 95.0, 1986.0, 256.0, 172.0, 623.0, 736.0, 0.0, 294.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-02', 'Feb', 351.0, 90.0, 0.0, 30.0, 0.0, 43.0, 0.0, 514.0, 514.0, 24.0, 489.0, 191.0, 104.0, 56.0, 0.0, 0.0, 163.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-03', 'Feb', 859.0, 0.0, 0.0, 0.0, 31.0, 90.0, 34.0, 1014.0, 980.0, 45.0, 935.0, 261.0, 85.0, 66.0, 0.0, 0.0, 569.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-04', 'Feb', 785.0, 0.0, 0.0, 0.0, 0.0, 50.0, 63.0, 898.0, 835.0, 40.0, 795.0, 188.0, 40.0, 392.0, 147.0, 18.0, 50.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-05', 'Feb', 1127.0, 0.0, 0.0, 0.0, 0.0, 340.0, 0.0, 1467.0, 1467.0, 69.0, 1399.0, 370.0, 405.0, 131.0, 221.0, 0.0, 131.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-06', 'Feb', 1287.0, 40.0, 0.0, 42.0, 48.0, 128.0, 62.0, 1607.0, 1545.0, 72.0, 1473.0, 65.0, 275.0, 722.0, 203.0, 0.0, 258.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-07', 'Feb', 1335.0, 0.0, 0.0, 0.0, 153.0, 121.0, 0.0, 1609.0, 1609.0, 75.0, 1534.0, 204.0, 551.0, 320.0, 189.0, 0.0, 274.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-08', 'Feb', 932.0, 0.0, 0.0, 0.0, 70.0, 153.0, 0.0, 1155.0, 1155.0, 52.0, 1103.0, 118.0, 215.0, 512.0, 87.0, 0.0, 223.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-09', 'Feb', 472.0, 34.0, 0.0, 0.0, 0.0, 160.0, 0.0, 666.0, 666.0, 63.0, 603.0, 63.0, 206.0, 203.0, 0.0, 0.0, 194.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-10', 'Feb', 824.0, 0.0, 35.0, 0.0, 0.0, 272.0, 8.0, 1138.0, 1131.0, 53.0, 1078.0, 105.0, 82.0, 637.0, 0.0, 0.0, 307.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-11', 'Feb', 707.0, 0.0, 0.0, 34.0, 75.0, 137.0, 0.0, 953.0, 953.0, 44.0, 909.0, 159.0, 118.0, 288.0, 142.0, 0.0, 246.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-12', 'Feb', 979.0, 0.0, 0.0, 0.0, 0.0, 177.0, 46.0, 1202.0, 1156.0, 55.0, 1102.0, 256.0, 502.0, 211.0, 0.0, 0.0, 177.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-13', 'Feb', 1001.0, 42.0, 116.0, 103.0, 0.0, 292.0, 39.0, 1592.0, 1553.0, 72.0, 1481.0, 161.0, 338.0, 346.0, 156.0, 0.0, 553.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-14', 'Feb', 6040.0, 52.0, 68.0, 0.0, 77.0, 268.0, 106.0, 6612.0, 6505.0, 308.0, 6197.0, 565.0, 3396.0, 373.0, 665.0, 22.0, 1486.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-15', 'Feb', 1135.0, 158.0, 83.0, 38.0, 101.0, 881.0, 169.0, 2565.0, 2396.0, 105.0, 2291.0, 20.0, 227.0, 434.0, 389.0, 66.0, 1261.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-16', 'Feb', 540.0, 0.0, 20.0, 0.0, 67.0, 268.0, 23.0, 918.0, 895.0, 41.0, 854.0, 97.0, 24.0, 217.0, 203.0, 0.0, 355.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-17', 'Feb', 264.0, 0.0, 99.0, 0.0, 48.0, 309.0, 0.0, 719.0, 719.0, 32.0, 688.0, 54.0, 87.0, 123.0, 0.0, 0.0, 456.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-18', 'Feb', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-19', 'Feb', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-20', 'Feb', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-21', 'Feb', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-22', 'Feb', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-23', 'Feb', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-24', 'Feb', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-25', 'Feb', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-26', 'Feb', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-27', 'Feb', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-02-28', 'Feb', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-01', 'Jan', 2478.0, 0.0, 40.0, 0.0, 127.0, 36.0, 24.0, 2705.0, 2681.0, 125.0, 2556.0, 54.0, 638.0, 636.0, 0.0, 0.0, 1354.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-01', 'Jan', 830.0, 0.0, 76.0, 0.0, 80.0, 296.0, 20.0, 1302.0, 1281.0, 60.0, 1222.0, 126.0, 319.0, 304.0, 81.0, 0.0, 452.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-03', 'Jan', 1288.0, 0.0, 111.0, 0.0, 0.0, 189.0, 30.0, 1618.0, 1588.0, 76.0, 1512.0, 211.0, 758.0, 279.0, 41.0, 0.0, 300.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-04', 'Jan', 1113.0, 0.0, 0.0, 30.0, 112.0, 162.0, 0.0, 1417.0, 1417.0, 65.0, 1351.0, 40.0, 298.0, 550.0, 225.0, 0.0, 304.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-05', 'Jan', 316.0, 0.0, 32.0, 0.0, 25.0, 50.0, 0.0, 423.0, 423.0, 20.0, 404.0, 74.0, 34.0, 208.0, 0.0, 0.0, 108.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-06', 'Jan', 664.0, 0.0, 0.0, 22.0, 61.0, 32.0, 0.0, 780.0, 780.0, 37.0, 743.0, 142.0, 169.0, 299.0, 55.0, 0.0, 116.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-07', 'Jan', 307.0, 0.0, 0.0, 0.0, 0.0, 35.0, 51.0, 393.0, 342.0, 16.0, 326.0, 151.0, 132.0, 24.0, 0.0, 0.0, 35.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-08', 'Jan', 963.0, 0.0, 0.0, 0.0, 52.0, 204.0, 162.0, 1381.0, 1219.0, 58.0, 1161.0, 409.0, 63.0, 242.0, 152.0, 97.0, 256.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-09', 'Jan', 738.0, 0.0, 95.0, 0.0, 77.0, 85.0, 5.0, 999.0, 995.0, 45.0, 950.0, 41.0, 382.0, 274.0, 41.0, 0.0, 257.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-10', 'Jan', 1229.0, 49.0, 0.0, 0.0, 147.0, 339.0, 20.0, 1783.0, 1764.0, 84.0, 1680.0, 144.0, 268.0, 641.0, 176.0, 0.0, 535.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-11', 'Jan', 1299.0, 164.0, 0.0, 0.0, 29.0, 475.0, 18.0, 1985.0, 1966.0, 92.0, 1874.0, 411.0, 179.0, 547.0, 163.0, 0.0, 668.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-11', 'Jan', 274.0, 0.0, 0.0, 26.0, 0.0, 280.0, 0.0, 580.0, 580.0, 27.0, 553.0, 132.0, 57.0, 85.0, 0.0, 0.0, 306.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-13', 'Jan', 993.0, 0.0, 0.0, 0.0, 0.0, 45.0, 0.0, 1038.0, 1038.0, 49.0, 988.0, 804.0, 85.0, 99.0, 0.0, 0.0, 45.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-14', 'Jan', 264.0, 0.0, 0.0, 28.0, 191.0, 250.0, 9.0, 742.0, 734.0, 32.0, 702.0, 17.0, 116.0, 54.0, 78.0, 0.0, 469.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-15', 'Jan', 612.0, 29.0, 61.0, 21.0, 73.0, 221.0, 10.0, 1028.0, 1017.0, 48.0, 969.0, 193.0, 100.0, 227.0, 94.0, 0.0, 405.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-16', 'Jan', 325.0, 0.0, 0.0, 0.0, 43.0, 228.0, 0.0, 595.0, 595.0, 27.0, 568.0, 14.0, 215.0, 97.0, 0.0, 271.0, 0.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-17', 'Jan', 965.0, 0.0, 24.0, 0.0, 0.0, 80.0, 6.0, 1075.0, 1069.0, 49.0, 1021.0, 7.0, 269.0, 639.0, 51.0, 0.0, 104.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-18', 'Jan', 638.0, 53.0, 120.0, 0.0, 82.0, 80.0, 119.0, 1092.0, 973.0, 46.0, 927.0, 27.0, 172.0, 264.0, 176.0, 0.0, 335.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-19', 'Jan', 513.0, 60.0, 90.0, 0.0, 0.0, 32.0, 28.0, 722.0, 694.0, 33.0, 661.0, 8.0, 115.0, 247.0, 143.0, 0.0, 182.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-20', 'Jan', 516.0, 0.0, 32.0, 0.0, 158.0, 123.0, 26.0, 855.0, 829.0, 37.0, 792.0, 221.0, 7.0, 182.0, 106.0, 0.0, 313.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-21', 'Jan', 288.0, 0.0, 0.0, 30.0, 0.0, 230.0, 4.0, 552.0, 549.0, 26.0, 522.0, 21.0, 120.0, 113.0, 34.0, 0.0, 260.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-21', 'Jan', 559.0, 0.0, 0.0, 0.0, 0.0, 54.0, 0.0, 613.0, 613.0, 28.0, 584.0, 221.0, 89.0, 124.0, 125.0, 0.0, 54.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-23', 'Jan', 494.0, 0.0, 66.0, 0.0, 74.0, 47.0, 0.0, 681.0, 681.0, 32.0, 648.0, 112.0, 185.0, 103.0, 94.0, 0.0, 187.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-24', 'Jan', 9236.0, 0.0, 0.0, 0.0, 28.0, 0.0, 0.0, 9264.0, 9264.0, 437.0, 8827.0, 96.0, 313.0, 249.0, 78.0, 0.0, 8528.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-25', 'Jan', 10114.0, 0.0, 0.0, 0.0, 230.0, 123.0, 44.0, 10511.0, 10467.0, 498.0, 9969.0, 202.0, 158.0, 248.0, 396.0, 0.0, 9463.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-26', 'Jan', 511.0, 0.0, 0.0, 0.0, 61.0, 405.0, 12.0, 988.0, 976.0, 42.0, 935.0, 145.0, 168.0, 198.0, 0.0, 0.0, 466.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-27', 'Jan', 536.0, 0.0, 0.0, 0.0, 72.0, 131.0, 24.0, 764.0, 740.0, 35.0, 705.0, 59.0, 60.0, 366.0, 52.0, 0.0, 204.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-28', 'Jan', 1381.0, 46.0, 84.0, 0.0, 0.0, 0.0, 51.0, 1562.0, 1511.0, 69.0, 1441.0, 4.0, 197.0, 183.0, 242.0, 0.0, 886.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-29', 'Jan', 1100.0, 0.0, 0.0, 15.0, 0.0, 36.0, 55.0, 1206.0, 1151.0, 49.0, 1102.0, 184.0, 248.0, 449.0, 220.0, 0.0, 51.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-30', 'Jan', 625.0, 0.0, 40.0, 146.0, 112.0, 324.0, 22.0, 1269.0, 1247.0, 56.0, 1191.0, 364.0, 16.0, 245.0, 0.0, 0.0, 622.0);
  insert into sales_transactions (company_id, sale_date, month, restaurant, keeta, careem, smile, talabat, noon, discount, gross_sale, net_sale_bt, tax, net_sale_at, cash, master_card, visa_card, zomato_paid, pay_later, online_pay) values (cid, '2026-01-31', 'Jan', 1772.0, 0.0, 0.0, 0.0, 38.0, 103.0, 64.0, 1976.0, 1912.0, 87.0, 1826.0, 554.0, 24.0, 621.0, 574.0, 0.0, 141.0);
  insert into recurring_expenses (company_id, category, month, amount) values (cid, 'Salaries', 'Jan', 13178.0);
  insert into recurring_expenses (company_id, category, month, amount) values (cid, 'Salaries', 'Feb', 18238.0);
  insert into recurring_expenses (company_id, category, month, amount) values (cid, 'Utilities', 'Jan', 6064.0);
  insert into recurring_expenses (company_id, category, month, amount) values (cid, 'Utilities', 'Feb', 2607.0);
  insert into recurring_expenses (company_id, category, month, amount) values (cid, 'Office Expenditure', 'Jan', 230.0);
  insert into recurring_expenses (company_id, category, month, amount) values (cid, 'Office Expenditure', 'Feb', 1580.0);
  insert into recurring_expenses (company_id, category, month, amount) values (cid, 'Staff Expenses', 'Jan', 2288.0);
  insert into recurring_expenses (company_id, category, month, amount) values (cid, 'Staff Expenses', 'Feb', 100.0);
  insert into recurring_expenses (company_id, category, month, amount) values (cid, 'Sundry Expenses', 'Jan', 2500.0);
  insert into recurring_expenses (company_id, category, month, amount) values (cid, 'Sundry Expenses', 'Feb', 2740.0);
  insert into recurring_expenses (company_id, category, month, amount) values (cid, 'Taxes', 'Jan', 2385.0);
  insert into recurring_expenses (company_id, category, month, amount) values (cid, 'Taxes', 'Feb', 1243.0);
  insert into monthly_cogs (company_id, month, cogs) values (cid, 'Jan', 17548.0) on conflict (company_id, month, fiscal_year) do update set cogs = excluded.cogs;
  insert into monthly_cogs (company_id, month, cogs) values (cid, 'Feb', 3208.0) on conflict (company_id, month, fiscal_year) do update set cogs = excluded.cogs;
  insert into balance_sheet_items (company_id, side, item, amount) values (cid, 'asset', 'Cash', NULL);
  insert into balance_sheet_items (company_id, side, item, amount) values (cid, 'asset', 'Accounts Receivable', NULL);
  insert into balance_sheet_items (company_id, side, item, amount) values (cid, 'asset', 'Inventory', NULL);
  insert into balance_sheet_items (company_id, side, item, amount) values (cid, 'asset', 'Non-Current (Fixed Assets)', NULL);
  insert into balance_sheet_items (company_id, side, item, amount) values (cid, 'asset', 'Furniture & Fixture', NULL);
  insert into balance_sheet_items (company_id, side, item, amount) values (cid, 'liability', 'Accounts Payable', NULL);
  insert into balance_sheet_items (company_id, side, item, amount) values (cid, 'liability', 'Short-term debt', NULL);
  insert into balance_sheet_items (company_id, side, item, amount) values (cid, 'liability', 'Long-term Debt', NULL);
  insert into balance_sheet_items (company_id, side, item, amount) values (cid, 'equity', 'Shareholders Equity', 300000.0);
  insert into balance_sheet_items (company_id, side, item, amount) values (cid, 'equity', 'Common Stock/ Capital', NULL);
  insert into balance_sheet_items (company_id, side, item, amount) values (cid, 'equity', 'Retained Earnings', NULL);
end $$;

-- Copy this UUID into Render env: ARCUS_COMPANY_ID
select id as arcus_company_id, name from companies where name = 'Arcus';

select 'sales' as table_name, count(*)::text as rows from sales_transactions
union all select 'recurring', count(*)::text from recurring_expenses
union all select 'cogs', count(*)::text from monthly_cogs
union all select 'balance_sheet', count(*)::text from balance_sheet_items
union all select 'receipts', count(*)::text from receipt_transactions;