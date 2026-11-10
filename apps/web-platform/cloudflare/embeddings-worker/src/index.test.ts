import { describe, expect, it, vi } from "vitest";
import worker from "./index";

const env = { EDGE_SHARED_SECRET: "test-secret", AI: { run: vi.fn(async () => ({ data: [[0.1, 0.2]] })) } };

describe("embeddings worker security", () => {
  it("rejects POST inference without Bearer authentication", async () => {
    const response = await worker.fetch(new Request("https://worker.test/embed", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: "hello" }),
    }), env);
    expect(response.status).toBe(401);
    expect(await response.json()).toMatchObject({ error: { code: "UNAUTHORIZED" } });
  });

  it("rejects an oversized request body with 413", async () => {
    const response = await worker.fetch(new Request("https://worker.test/embed", {
      method: "POST",
      headers: { Authorization: "Bearer test-secret", "Content-Type": "application/json" },
      body: JSON.stringify({ text: "x".repeat(256 * 1024) }),
    }), env);
    expect(response.status).toBe(413);
    expect(await response.json()).toMatchObject({ error: { code: "PAYLOAD_TOO_LARGE" } });
  });

  it("fails closed when the shared secret is absent", async () => {
    const response = await worker.fetch(new Request("https://worker.test/embed", {
      method: "POST", body: JSON.stringify({ text: "hello" }),
    }), { AI: env.AI });
    expect(response.status).toBe(500);
    expect(await response.json()).toMatchObject({ error: { code: "AUTH_NOT_CONFIGURED" } });
  });
  it("rejects batches larger than 32 inputs", async () => {
    const response = await worker.fetch(new Request("https://worker.test/embed", {
      method: "POST",
      headers: { Authorization: "Bearer test-secret", "Content-Type": "application/json" },
      body: JSON.stringify({ texts: Array.from({ length: 33 }, () => "hello") }),
    }), env);
    expect(response.status).toBe(413);
    expect(await response.json()).toMatchObject({ error: { code: "BATCH_TOO_LARGE" } });
  });

  it("rejects requests with no text input", async () => {
    const response = await worker.fetch(new Request("https://worker.test/embed", {
      method: "POST",
      headers: { Authorization: "Bearer test-secret", "Content-Type": "application/json" },
      body: JSON.stringify({}),
    }), env);
    expect(response.status).toBe(400);
    expect(await response.json()).toMatchObject({ error: { code: "MISSING_INPUT" } });
  });

});
