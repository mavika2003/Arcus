import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const maxDuration = 60;

function backendBase(): string {
  const raw =
    process.env.API_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    process.env.NEXT_PUBLIC_BACKEND_URL ??
    "http://127.0.0.1:8000";
  let url = raw.trim().replace(/\/$/, "");
  if (!/^https?:\/\//i.test(url)) url = `https://${url}`;
  return url;
}

/** Proxy receipt OCR to Render (same-origin for browser; no CORS). */
export async function POST(req: NextRequest) {
  const form = await req.formData();
  const upstream = await fetch(`${backendBase()}/api/upload-receipt`, {
    method: "POST",
    body: form,
  });

  const body = await upstream.text();
  return new NextResponse(body, {
    status: upstream.status,
    headers: {
      "Content-Type": upstream.headers.get("content-type") ?? "application/json",
    },
  });
}
