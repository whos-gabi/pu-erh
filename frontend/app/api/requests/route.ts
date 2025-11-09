import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "../auth/[...nextauth]/route";
import { API_BASE_URL } from "@/lib/api";

export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session || !session.user?.token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  try {
    const response = await fetch(`${API_BASE_URL}api/requests/`, {
      headers: {
        Authorization: `Bearer ${session.user.token}`,
        accept: "application/json",
      },
      cache: "no-store",
    });
    const contentType = response.headers.get("content-type") || "";
    if (!response.ok) {
      const text = await response.text();
      return NextResponse.json(
        { error: "Failed to fetch API", details: text },
        { status: response.status }
      );
    }
    if (contentType.includes("application/json")) {
      const data = await response.json();
      return NextResponse.json(data);
    }
    const text = await response.text();
    return NextResponse.json(
      { error: "API did not return JSON", details: text },
      { status: 500 }
    );
  } catch {
    return NextResponse.json(
      { error: "Upstream request failed" },
      { status: 502 }
    );
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.text();
    const auth = req.headers.get("authorization") || "";
    const upstream = await fetch(`${API_BASE_URL}api/requests/`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: auth,
      },
      body,
      cache: "no-store",
    });
    const text = await upstream.text();
    return new Response(text, {
      status: upstream.status,
      headers: {
        "content-type":
          upstream.headers.get("content-type") || "application/json",
      },
    });
  } catch {
    return new Response(JSON.stringify({ error: "Upstream request failed" }), {
      status: 502,
      headers: { "content-type": "application/json" },
    });
  }
}
