# 🧠 Cognix Nexus
> **Personal Knowledge OS, Research Intelligence & Second Brain Platform**

[![Next.js](https://img.shields.io/badge/Next.js-15-black?style=flat-square&logo=next.js)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Python_3.12-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React Native](https://img.shields.io/badge/React_Native-Expo-000020?style=flat-square&logo=expo)](https://expo.dev/)
[![Supabase](https://img.shields.io/badge/Supabase-pgvector_&_Database-3ECF8E?style=flat-square&logo=supabase)](https://supabase.com/)
[![Gemini AI](https://img.shields.io/badge/Gemini_2.0-Flash_Synthesis-4285F4?style=flat-square&logo=google)](https://deepmind.google/technologies/gemini/)
[![Groq](https://img.shields.io/badge/Groq-Fast_Inference-F55036?style=flat-square)](https://groq.com/)
[![Cloudinary](https://img.shields.io/badge/Cloudinary-Media_Storage-3448C5?style=flat-square&logo=cloudinary)](https://cloudinary.com/)
[![Render](https://img.shields.io/badge/Render-Backend_Live-46E3B7?style=flat-square&logo=render)](https://cognix-core-ypak.onrender.com)
[![Vercel](https://img.shields.io/badge/Vercel-Frontend_Live-black?style=flat-square&logo=vercel)](https://cognix-nexus.vercel.app)
[![Telegram](https://img.shields.io/badge/Telegram_Bot-Topic_#7-26A5E4?style=flat-square&logo=telegram)](https://t.me/)

---

## 🌟 Overview

**Cognix Nexus** (evolving into **Cognix Brain Vault**) is a personal knowledge operating system built on a research intelligence foundation.

It captures research sources, distills raw claims into verified knowledge, constructs concept graph relationships, and serves proactive recall, spaced repetition, and deep synthesis through a hybrid RAG engine.

---

## 🚀 Key Features

* **🕸️ Concept Graph & Knowledge Network**: Visual, node-based interactive graph linking concepts, citations, and evidence.
* **🔬 Evidence-First Ingestion**: Research sources ➔ processing ➔ evidence/claims ➔ human review ➔ approved knowledge in Brain Vault.
* **📚 Spaced Repetition (SM-2)**: Built-in active recall and flashcard quizzing algorithm for optimal memory retention.
* **🧠 Hybrid RAG Engine**: Gemini 2.0 Flash & Groq paired with Supabase vector search (`pgvector`) for precise context retrieval.
* **📱 Omnichannel Capture**: Web, Mobile (Expo), Google Drive sync, and Telegram Bot (Topic `#7`) for quick memo ingestion.
* **🎙️ Media Intelligence (Vizora Lens)**: Audio memo transcription, video frame synthesis, and cross-lingual concept tagging.

---

## 🏗️ System Architecture

```
       Research Sources (Web / PDF / Audio / Books / Telegram)
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                 Cognix Core Processing Pipeline               │
│   • Claim Extractor • Entity Linker • Embeddings Generator   │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                 Durable Personal Brain Vault                  │
│   • Supabase pgvector • Graph Relations • Concept Nodes       │
│   • SM-2 Memory Matrix • Cloudinary Image / Media Assets      │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                 Knowledge Synthesis Interfaces                │
│   • Next.js 15 Web Command UI (Vercel)                       │
│   • Expo Mobile Knowledge Assistant (iOS / Android)           │
│   • Telegram Brain Capture Bot (@CognixNexusBot in Topic #7)  │
└───────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quickstart

```bash
# 1. Backend Setup
cd apps/web-platform/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. Frontend Setup
cd ../frontend
pnpm install
pnpm dev
```

---

## 📜 License

Private Knowledge OS License. All Rights Reserved.
