import { API_BASE_URL } from "@/lib/api";

export async function GET(req: Request) {
  const auth = req.headers.get("authorization") || "";
  try {
    const upstream = await fetch(`${API_BASE_URL}api/users/me/`, {
      headers: {
        authorization: auth,
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


