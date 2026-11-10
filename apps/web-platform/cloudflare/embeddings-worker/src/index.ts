export interface Env {
  AI: { run(model: string, options: { text: string[] }): Promise<{ data?: number[][] }> };
  EDGE_SHARED_SECRET?: string;
  ALLOWED_ORIGIN?: string;
}

// Per-isolate buckets are a best-effort guard; configure Cloudflare Rate Limiting
// at the edge for distributed enforcement across isolates/regions.
const buckets = new Map<string, { window: number; count: number }>();
const WINDOW_MS = 60_000;
const LIMIT = 30;
const MAX_BODY_BYTES = 256 * 1024;

function corsHeaders(origin: string, allowedOrigin?: string): HeadersInit {
  const allow = allowedOrigin || "*";
  return {
    "Access-Control-Allow-Origin": origin === allow || allow === "*" ? origin : allow,
    "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Cognix-Trace",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Vary": "Origin",
  };
}
function json(body: unknown, status: number, origin: string, env: Env): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json", ...corsHeaders(origin, env.ALLOWED_ORIGIN) },
  });
}
function constantTimeEqual(a: string, b: string): boolean {
  const encoder = new TextEncoder();
  const aa = encoder.encode(a), bb = encoder.encode(b);
  let diff = aa.length ^ bb.length;
  const max = Math.max(aa.length, bb.length);
  for (let i = 0; i < max; i++) diff |= (aa[i] || 0) ^ (bb[i] || 0);
  return diff === 0;
}
function rateLimited(key: string, now = Date.now()): boolean {
  const bucket = buckets.get(key);
  if (!bucket || now - bucket.window >= WINDOW_MS) {
    buckets.set(key, { window: now, count: 1 });
    return false;
  }
  bucket.count += 1;
  return bucket.count > LIMIT;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";
    if (request.method === "OPTIONS") return new Response(null, { status: 204, headers: corsHeaders(origin, env.ALLOWED_ORIGIN) });
    if (url.pathname === "/health" || url.pathname === "/") return json({ status: "ok", service: "cognix-nexus-embeddings", model: "@cf/baai/bge-large-en-v1.5" }, 200, origin, env);
    if (request.method !== "POST") return json({ error: { code: "METHOD_NOT_ALLOWED", message: "Method not allowed" } }, 405, origin, env);

    if (!env.EDGE_SHARED_SECRET) return json({ error: { code: "AUTH_NOT_CONFIGURED", message: "Inference authentication is not configured" } }, 500, origin, env);
    const authHeader = request.headers.get("Authorization") || "";
    const match = /^Bearer ([^\s]+)$/i.exec(authHeader);
    if (!match || !constantTimeEqual(match[1], env.EDGE_SHARED_SECRET)) return json({ error: { code: "UNAUTHORIZED", message: "Bearer authentication required" } }, 401, origin, env);

    const ip = request.headers.get("CF-Connecting-IP") || request.headers.get("X-Forwarded-For")?.split(",")[0]?.trim() || "unknown";
    // Bound map growth by periodically pruning expired buckets.
    const now = Date.now();
    if (buckets.size > 5000) for (const [key, value] of buckets) if (now - value.window >= WINDOW_MS) buckets.delete(key);
    if (rateLimited("ip:" + ip, now) || rateLimited("token:" + match[1], now)) return json({ error: { code: "RATE_LIMITED", message: "Rate limit exceeded" } }, 429, origin, env);

    const lengthHeader = Number(request.headers.get("Content-Length") || 0);
    if (lengthHeader > MAX_BODY_BYTES) return json({ error: { code: "PAYLOAD_TOO_LARGE", message: "Request body exceeds 256 KB" } }, 413, origin, env);
    try {
      const raw = await request.text();
      if (new TextEncoder().encode(raw).byteLength > MAX_BODY_BYTES) return json({ error: { code: "PAYLOAD_TOO_LARGE", message: "Request body exceeds 256 KB" } }, 413, origin, env);
      let body: { text?: string | string[]; texts?: string[]; model?: string };
      try { body = JSON.parse(raw); } catch { return json({ error: { code: "INVALID_JSON", message: "Request body must be valid JSON" } }, 400, origin, env); }
      const rawInputs = body.texts || (Array.isArray(body.text) ? body.text : body.text ? [body.text] : []);
      if (!Array.isArray(rawInputs) || rawInputs.length === 0) return json({ error: { code: "MISSING_INPUT", message: "Missing 'text' or 'texts' field" } }, 400, origin, env);
      if (rawInputs.length > 32) return json({ error: { code: "BATCH_TOO_LARGE", message: "Batch size must be at most 32" } }, 413, origin, env);
      if (rawInputs.some((item) => typeof item !== "string" || item.length > 4000)) return json({ error: { code: "INPUT_TOO_LARGE", message: "Each input must be a string of at most 4000 characters" } }, 413, origin, env);
      const inputs = rawInputs as string[];
      const modelName = body.model || "@cf/baai/bge-large-en-v1.5";
      const output = await env.AI.run(modelName, { text: inputs });
      const data = (output.data || []).map((emb: number[], idx: number) => ({ object: "embedding", embedding: emb, index: idx }));
      return json({ object: "list", data, model: modelName, usage: { prompt_tokens: inputs.reduce((acc, str) => acc + Math.ceil(str.length / 4), 0), total_tokens: 0 } }, 200, origin, env);
    } catch {
      return json({ error: { code: "INFERENCE_FAILED", message: "Embedding inference failed" } }, 500, origin, env);
    }
  },
};
