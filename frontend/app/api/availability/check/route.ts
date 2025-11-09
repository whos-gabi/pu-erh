import { API_BASE_URL } from "@/lib/api";

export async function GET(req: Request) {
  const url = new URL(req.url);
  const date = url.searchParams.get("date") || "";
  const user_id = url.searchParams.get("user_id") || "";
  const auth = req.headers.get("authorization") || "";

  const upstreamUrl = new URL(`${API_BASE_URL}api/availability/check/`);
  if (date) upstreamUrl.searchParams.set("date", date);
  if (user_id) upstreamUrl.searchParams.set("user_id", user_id);

  try {
    const upstream = await fetch(upstreamUrl.toString(), {
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


