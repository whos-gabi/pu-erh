import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "../auth/[...nextauth]/route";
import { API_BASE_URL } from "@/lib/api";

export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions);
  if (!session || !session.user?.token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Example: fetch data from your external API using the session token
  const token = session.user.token;

  const { searchParams } = new URL(req.url);
  const room = searchParams.get("roomCode");
  const date = searchParams.get("date");

  console.log("Room:", room);
  console.log("Date:", date);

  const url = `https://api.desepticon.qzz.io/api/requests/by-room-and-date/?roomCode=${room}&date=${date}`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      accept: "application/json",
    },
  });
  console.log(response);

  const contentType = response.headers.get("content-type");

  if (!response.ok) {
    const text = await response.text(); // could be HTML
    console.error("API error:", text);
    return NextResponse.json(
      { error: "Failed to fetch API", details: text },
      { status: response.status }
    );
  }

  if (contentType && contentType.includes("application/json")) {
    const data = await response.json();
    return NextResponse.json(data);
  } else {
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
