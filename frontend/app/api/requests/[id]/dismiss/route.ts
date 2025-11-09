import { NextResponse } from "next/server";

export async function POST(
  req: Request,
  context: { params: Promise<{ id: string }> }
) {
  const { id } = await context.params; // FIX
  const backendUrl = `https://api.desepticon.qzz.io/api/requests/${id}/dismiss`; // FIXED URL

  const body = await req.json();

  const res = await fetch(backendUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: req.headers.get("Authorization") || "",
    },
    body: JSON.stringify(body),
  });

  const data = await res.json();
  return NextResponse.json(data, { status: res.status });
}
