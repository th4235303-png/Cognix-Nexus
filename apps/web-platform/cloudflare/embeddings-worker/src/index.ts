export interface Env {
  AI: any;
  EDGE_SHARED_SECRET?: string;
  ALLOWED_ORIGIN?: string;
}

function corsHeaders(origin: string, allowedOrigin?: string): HeadersInit {
  const allow = allowedOrigin || "*";
  return {
    "Access-Control-Allow-Origin": origin === allow || allow === "*" ? origin : allow,
    "Access-Control-Allow-Headers": "Authorization, Content-Type, X-Cognix-Trace",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Vary": "Origin",
  };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const origin = request.headers.get("Origin") || "";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders(origin, env.ALLOWED_ORIGIN) });
    }

    if (url.pathname === "/health" || url.pathname === "/") {
      return new Response(JSON.stringify({ status: "ok", service: "cognix-nexus-embeddings", model: "@cf/baai/bge-large-en-v1.5" }), {
        status: 200,
        headers: { "Content-Type": "application/json", ...corsHeaders(origin, env.ALLOWED_ORIGIN) },
      });
    }

    if (request.method !== "POST") {
      return new Response(JSON.stringify({ error: "Method not allowed" }), {
        status: 405,
        headers: { "Content-Type": "application/json", ...corsHeaders(origin, env.ALLOWED_ORIGIN) },
      });
    }

    // Shared Secret validation if configured
    if (env.EDGE_SHARED_SECRET) {
      const authHeader = request.headers.get("Authorization") || "";
      const token = authHeader.replace(/^Bearer\s+/i, "").trim();
      if (token !== env.EDGE_SHARED_SECRET) {
        return new Response(JSON.stringify({ error: "Unauthorized" }), {
          status: 401,
          headers: { "Content-Type": "application/json", ...corsHeaders(origin, env.ALLOWED_ORIGIN) },
        });
      }
    }

    try {
      const body = (await request.json()) as { text?: string | string[]; texts?: string[]; model?: string };
      const rawInputs = body.texts || (Array.isArray(body.text) ? body.text : body.text ? [body.text] : []);

      if (!rawInputs || rawInputs.length === 0) {
        return new Response(JSON.stringify({ error: "Missing 'text' or 'texts' field" }), {
          status: 400,
          headers: { "Content-Type": "application/json", ...corsHeaders(origin, env.ALLOWED_ORIGIN) },
        });
      }

      // Truncate to reasonable length per item to prevent OOM
      const inputs = rawInputs.slice(0, 32).map(t => String(t).slice(0, 4000));
      const modelName = body.model || "@cf/baai/bge-large-en-v1.5";

      const output = await env.AI.run(modelName, {
        text: inputs,
      });

      // Format in OpenAI embeddings format for universal client compatibility
      const data = (output.data || []).map((emb: number[], idx: number) => ({
        object: "embedding",
        embedding: emb,
        index: idx,
      }));

      return new Response(
        JSON.stringify({
          object: "list",
          data,
          model: modelName,
          usage: { prompt_tokens: inputs.reduce((acc, str) => acc + Math.ceil(str.length / 4), 0), total_tokens: 0 },
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json", ...corsHeaders(origin, env.ALLOWED_ORIGIN) },
        }
      );
    } catch (err: any) {
      return new Response(JSON.stringify({ error: "Embedding inference failed", detail: err?.message || String(err) }), {
        status: 500,
        headers: { "Content-Type": "application/json", ...corsHeaders(origin, env.ALLOWED_ORIGIN) },
      });
    }
  },
};
