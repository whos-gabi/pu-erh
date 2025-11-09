import { API_BASE_URL } from "@/lib/api";
import type { NextRequest } from "next/server";

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const item_id = url.searchParams.get("item_id") || "";
  const auth = req.headers.get("authorization") || "";
  const upstreamUrl = new URL(`${API_BASE_URL}api/item-occupancy-stats/stats/`);
  if (item_id) upstreamUrl.searchParams.set("item_id", item_id);
  try {
    const upstream = await fetch(upstreamUrl.toString(), {
      headers: {
        authorization: auth,
        accept: "application/json",
      },
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
    return new Response(JSON.stringify({ error: "Upstream fetch failed" }), {
      status: 502,
      headers: { "content-type": "application/json" },
    });
  }
}


