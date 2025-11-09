import { API_BASE_URL } from "@/lib/api";

export async function GET(req: Request, context: { params: { id?: string } }) {
  // Be defensive: get id from params or URL path
  let id = context.params?.id;
  if (!id) {
    try {
      const url = new URL(req.url);
      const parts = url.pathname.split("/").filter(Boolean); // ["api","users","{id}"]
      const idx = parts.findIndex((p) => p === "users");
      if (idx !== -1 && parts[idx + 1]) {
        id = parts[idx + 1];
      }
    } catch {
      // ignore
    }
  }
  const auth = req.headers.get("authorization") || "";
  if (!id) {
    return new Response(JSON.stringify({ error: "Missing user id" }), {
      status: 400,
      headers: { "content-type": "application/json" },
    });
  }
  try {
    const upstream = await fetch(`${API_BASE_URL}api/users/${id}/`, {
      headers: {
        authorization: auth,
      },
      // Avoid caching user profile
      cache: "no-store",
    });
    const text = await upstream.text();
    return new Response(text, {
      status: upstream.status,
      headers: { "content-type": upstream.headers.get("content-type") || "application/json" },
    });
  } catch (e) {
    return new Response(JSON.stringify({ error: "Upstream fetch failed" }), {
      status: 502,
      headers: { "content-type": "application/json" },
    });
  }
}


