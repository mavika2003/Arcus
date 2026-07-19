FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-ara \
    poppler-utils \
    libheif1 \
    && rm -rf /var/lib/apt/lists/*

ENV TESSERACT_CMD=/usr/bin/tesseract

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY src ./src
COPY supabase ./supabase
COPY data ./data
COPY Sales ./Sales
COPY Expenses ./Expenses
COPY ["Balance Sheet - Sheet1.csv", "./"]
COPY ["P&L - Sheet1.csv", "./"]

ENV PORT=8000
EXPOSE 8000
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}
