import { NextRequest, NextResponse } from "next/server";
import { getServerSession } from "next-auth/next";
import { authOptions } from "../auth/[...nextauth]/route"; // adjust path to your auth options

export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions);

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Example: fetch data from your external API using the session token
  const token = session.user.token;

  console.log(token);

  const response = await fetch("https://api.desepticon.qzz.io/api/requests", {
    headers: {
      Authorization: `Bearer ${token}`,
      accept: "application/json",
    },
  });

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
    console.error("API did not return JSON:", text);
    return NextResponse.json(
      { error: "API did not return JSON", details: text },
      { status: 500 }
    );
  }
}
