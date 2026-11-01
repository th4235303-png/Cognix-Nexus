# Cognix Nexus — Cloudflare Workers AI Embeddings Worker

Edge embedding engine running `@cf/baai/bge-large-en-v1.5` on Cloudflare Workers AI with zero cloud GPU fees.

## Deployment

```bash
cd apps/web-platform/cloudflare/embeddings-worker
npm install
npx wrangler deploy
```

## Backend Configuration

Set in `apps/web-platform/backend/.env`:
```env
CLOUDFLARE_EMBEDDINGS_URL=https://cognix-nexus-embeddings.<your-subdomain>.workers.dev
EDGE_SHARED_SECRET=<your-edge-secret>
```
