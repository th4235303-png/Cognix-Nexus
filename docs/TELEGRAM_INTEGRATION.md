# Telegram Integration Guide: Cognix-Nexus

> **Project:** Cognix-Nexus / Brain Vault (Personal Knowledge OS & Research Intelligence)  
> **Directory:** `th4235303@gmail.com\Cognix-Nexus`  
> **Runtime / Stack:** FastAPI (Python), Render  
> **Primary Topic:** `🧠 Cognix-Nexus`

---

## 1. Overview & Topic Role

Cognix-Nexus (Brain Vault) uses the Telegram Supergroup for research capture and active learning:
* Alerts when books or papers are distilled into atomic concepts.
* Extraction reports for research claims and evidence.
* Automated daily flashcards using spaced-repetition algorithms.
* Knowledge vault synchronization notifications.

Users can review flashcards and recall ratings with inline buttons (`I Knew This` / `Review Again`).

---

## 2. Topic Configuration

* **Suggested Topic Name:** `🧠 Cognix-Nexus`
* **Suggested Topic ID:** `3` (or your assigned `message_thread_id`)
* **Color / Icon:** 🧠 Brain / Knowledge

---

## 3. Environment Variables

Configure these variables in `web-platform/backend/.env` or in the Render Dashboard:

| Key | Type | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | String (Secret) | `""` | Bot token provided by `@BotFather` |
| `TELEGRAM_CHAT_ID` | String | `""` | Supergroup ID (e.g. `-100xxxxxxxxxx`) |
| `TELEGRAM_TOPIC_ID` | Integer | `None` | Thread ID for `#Cognix-Nexus` topic |
| `TELEGRAM_ENABLED` | Boolean | `false` | Master toggle (`true` to enable delivery) |

---

## 4. Code Architecture

* **Service Module:** `web-platform/backend/app/services/telegram.py`
* **Configuration:** Environment resolution via `os.getenv`
* **Template:** `web-platform/backend/.env.example`

---

## 5. Available Action Hooks & API

### (1) Book Distillation Notification
```python
from app.services.telegram import notify_book_distilled

await notify_book_distilled(
    book_title="Thinking, Fast and Slow",
    insights_count=24,
    summary_snippet="Explores the dual-system model of cognitive processing (System 1 vs System 2)."
)
```
* **Actions included:**
  - `[🧠 View in Brain Vault]` (`cognix_vault_book:Thinking, Fast and Slow`)

### (2) Research Ingested Notification
```python
from app.services.telegram import notify_research_ingested

await notify_research_ingested(
    source_title="Transformer Architectures in Logistics Optimization",
    claims_count=18
)
```

### (3) Daily Spaced Repetition Flashcard
```python
from app.services.telegram import notify_daily_flashcard

await notify_daily_flashcard(
    card_id="fc_401",
    concept="Bayesian Updating",
    question="How do prior beliefs adjust upon receiving new observed evidence?"
)
```
* **Actions included:**
  - `[💡 Reveal Answer]` (`cognix_reveal:fc_401`)
  - `[✅ I Knew This]` (`cognix_grade_easy:fc_401`)
  - `[❌ Review Again]` (`cognix_grade_hard:fc_401`)

### (4) Vault Synchronization Status
```python
from app.services.telegram import notify_vault_sync

await notify_vault_sync(items_count=142)
```

---

## 6. Cloud Deployment Checklist (Render)

1. Open Render dashboard -> Cognix backend service.
2. Go to **Environment** tab.
3. Add `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TELEGRAM_TOPIC_ID`, and set `TELEGRAM_ENABLED=true`.
4. Save and deploy.

---

## 7. Inbound Action Handler API

This project includes a dedicated inbound endpoint to receive callbacks from the Central Cloudflare Gateway:
* **Endpoint:** `POST /telegram/action`
* **Supported Actions:**
  * `cognix_reveal:<id>` -> Reveals the hidden answer/explanation for a spaced-repetition card
  * `cognix_grade_easy:<id>` -> Increases review interval (+4 days) for mastered knowledge
  * `cognix_grade_hard:<id>` -> Resets interval to 1 day for repeated practice
  * `cognix_quick_capture` -> Ingests forwarded Telegram link or note straight into the Brain Vault inbox

---

## 8. AI Provider & API Keys Configuration

| Provider | Environment Key | Primary Role in Cognix Core / Nexus | Free / Paid Notes |
|---|---|---|---|
| **OpenRouter** | `OPENROUTER_API_KEY` | Secondary LLM fallback & free embeddings | `openrouter/free` (50 req/day) |
| **Groq** | `GROQ_API_KEY` | Ultra-fast claim extraction & note summarization | `qwen/qwen3.8-27b` (14,400 req/day free) |
| **Mistral** | `MISTRAL_API_KEY` | Deep book chapter distillation & concept mapping | `ministral-8b-latest` |
| **Cohere** | `COHERE_API_KEY` | Multi-stage document reranking & 1536-dim embeddings | `command-a-03-2025` & `embed-v4.0` |
| **Cloudflare** | `CLOUDFLARE_API_TOKEN`<br>`CLOUDFLARE_ACCOUNT_ID` | Fast serverless reasoning & BGE embeddings | `@cf/meta/llama-3.1-8b`, `@cf/baai/bge-large-en-v1.5` |
| **Voyage** | `VOYAGE_API_KEY` | High-fidelity research semantic embeddings | `voyage-4` (supports 256, 512, 1024, 2048 dims) |
| **Hugging Face** | `HUGGINGFACE_API_KEY` | Myanmar tokenizers & dataset downloads | Inference API disabled (Oct 8); Hub/Spaces only |

---

## 9. Tuned Fallback Chains & AI Monitoring

### 💬 Chat & Research Synthesis Chain
1. 🥇 **Gemini 2.5/3.5-flash** — Primary for complex multi-source research reasoning and Burmese analysis.
2. 🥈 **Groq (`qwen/qwen3.8-27b`)** — Ultra-fast summarization & card extraction (14,400 req/day free).
3. 🥉 **Cohere (`command-a-03-2025`)** — High-precision conceptual linking.
4. 4️⃣ **Cloudflare Workers AI (`llama-3.1-8b`)** — Serverless resilience.
5. 5️⃣ **OpenRouter (Free models)** — Emergency quota fallback (50 req/day).

### 📚 Knowledge Graph & RAG Embeddings (1536-D Vector)
1. 🥇 **Voyage AI (`voyage-4`, 1536-D)** — High semantic precision.
2. 🥈 **Cohere (`embed-v4.0`, 1536-D)** — Direct fallback matching database dimension.
3. 🥉 **Cloudflare (`bge-large`)** / OpenRouter.

### 📊 Real-Time AI Usage & Health API
* **Endpoint:** `GET /usage/ai` & `GET /usage`
* **Telegram Command:** Send `/ai_status` or click `[🔄 Refresh Usage]` in Telegram to view active provider states and daily call counts.


