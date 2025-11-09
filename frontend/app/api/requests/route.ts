import { API_BASE_URL } from "@/lib/api";

export async function POST(req: Request) {
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


