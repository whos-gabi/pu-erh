import { NextResponse } from "next/server";

export async function POST(
  req: Request,
  { params }: { params: { id: string } }
) {
  const id = params.id;
  const backendUrl = `https://api.desepticon.qzz.io/api/requests/${id}/approve/`;
  console.log("->>>>>", backendUrl);

  const body = await req.json();

  const res = await fetch(backendUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: req.headers.get("Authorization") || "",
    },
    body: JSON.stringify(body),
  });

  const raw = await res.text();
  console.log("BACKEND RESPONSE:", raw);

  let data;
  try {
    data = JSON.parse(raw);
  } catch {
    return NextResponse.json(
      { error: "Backend did not return JSON", raw },
      { status: 500 }
    );
  }

  return NextResponse.json(data, { status: res.status });
}
