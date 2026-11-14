const HOP_BY_HOP = new Set([
  "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
  "te", "trailer", "transfer-encoding", "upgrade",
]);

function corsHeaders(origin, allowedOrigin) {
  const allow = allowedOrigin || "*";
  return {
    "Access-Control-Allow-Origin": origin === allow || allow === "*" ? origin : allow,
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,PATCH,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Requested-With,X-Cognix-Signature",
    "Access-Control-Max-Age": "86400",
    "Vary": "Origin",
  };
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin, env.ALLOWED_ORIGIN) });
    }

    const upstreamBase = (env.UPSTREAM_API || "https://cognix-core-ypak.onrender.com").trim().replace(/\/$/, "");

    // Health check endpoint
    if (url.pathname === "/health" || url.pathname === "/api/health") {
      return new Response(
        JSON.stringify({
          status: "healthy",
          service: "cognix-nexus-edge",
          region: request.cf ? request.cf.colo : "global",
          upstream: upstreamBase,
          timestamp: new Date().toISOString(),
        }),
        {
          status: 200,
          headers: {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            ...corsHeaders(origin, env.ALLOWED_ORIGIN),
          },
        }
      );
    }

    const targetUrl = new URL(upstreamBase + url.pathname + url.search);
    const headers = new Headers(request.headers);
    for (const h of HOP_BY_HOP) {
      headers.delete(h);
    }

    headers.set("X-Cognix-Edge", "cloudflare-worker");
    headers.set("X-Forwarded-Host", url.host);
    headers.set("X-Forwarded-Proto", url.protocol.replace(":", ""));

    const isBodyMethod = request.method !== "GET" && request.method !== "HEAD";
    const upstreamReq = new Request(targetUrl.toString(), {
      method: request.method,
      headers,
      body: isBodyMethod ? request.body : undefined,
      redirect: "manual",
    });

    try {
      const upstreamRes = await fetch(upstreamReq);
      const resHeaders = new Headers(upstreamRes.headers);
      const cors = corsHeaders(origin, env.ALLOWED_ORIGIN);
      for (const [k, v] of Object.entries(cors)) {
        resHeaders.set(k, v);
      }
      return new Response(upstreamRes.body, {
        status: upstreamRes.status,
        statusText: upstreamRes.statusText,
        headers: resHeaders,
      });
    } catch (err) {
      return new Response(
        JSON.stringify({
          error: "Upstream service unavailable",
          detail: err.message || String(err),
        }),
        {
          status: 502,
          headers: {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            ...corsHeaders(origin, env.ALLOWED_ORIGIN),
          },
        }
      );
    }
  },
};
