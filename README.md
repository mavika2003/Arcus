# Arcus — Restaurant Financial Dashboard

Next.js frontend + Python FastAPI backend for P&L and Balance Sheet tracking.

## Stack

- **Frontend:** Next.js 16, TypeScript, Tailwind CSS, Plotly.js
- **Backend:** FastAPI, Pandas, openpyxl, numbers-parser

## Quick Start

### 1. Python backend

```bash
cd /Users/malvikasawant/Documents/Arcus
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

### 2. Next.js frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Data Files

Place your source files in `data/raw/` (defaults are already copied):

- `Daily Sales 2.numbers` — daily transactions, tax, payment modes
- `P&L Account.xlsx` — P&L, Daily Expenses, Recurring Cost, Balance Sheet sheets

Upload updated files via the **Tools** tab in the dashboard.

## Project Structure

```
Arcus/
├── frontend/          # Next.js UI (FORGE dark theme)
├── backend/           # FastAPI REST API
├── src/               # Python data pipeline
│   ├── data/          # loaders, cleaners, validators
│   ├── calculations/  # P&L, balance sheet math
│   ├── services/      # categorizer, alerts, export
│   └── pipeline.py    # orchestrator
└── data/raw/          # default data files
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dashboard` | Full dashboard JSON |
| POST | `/api/dashboard/upload` | Upload sales + P&L files |
| POST | `/api/categorize` | AI expense categorization |
| GET | `/api/export/excel` | Download Excel report |
| GET | `/api/export/pdf` | Download PDF report |
