import { supabase } from '@/lib/supabase';

const configuredApiUrl = (process.env.NEXT_PUBLIC_COGNIX_API_URL || '').trim();
if (process.env.NODE_ENV === 'production' && !configuredApiUrl) {
  throw new Error('NEXT_PUBLIC_COGNIX_API_URL must be set in production');
}
const API_BASE_URL = (configuredApiUrl || 'http://localhost:8000').replace(/\/$/, '');
const API_PREFIX = '/v1';

import type { Source, SourceStatus, SourceType, TrustLevel } from '@/lib/types/source';

export interface ApiClaim { id: string; text: string; excerpt?: string | null; location?: string | null; confidence: string; verification_state: string; created_at: string; }
export interface ApiSource { id: string; url: string; note?: string | null; status: string; processing_stage: string; created_at: string; updated_at: string; critical_warnings: string[]; claims?: ApiClaim[]; source_trust?: string; original_text?: string | null; ai_summary?: string | null; myanmar_translation?: string | null; human_edited_myanmar?: string | null; approved_myanmar?: string | null; key_points?: string[]; }
export interface ApiProcessingTask { id: string; source_id: string; stage: string; progress: number; status: string; retry_count: number; error: string | null; }
export interface ApiExportJob { id: string; source_id: string; status: string; idempotency_key: string; drive_reference: string | null; files: string[]; error?: string | null; }
export interface ApiUsage { ai_requests_today: number; processing_jobs: number; translation_requests: number; drive_exports: number; }

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, detail: unknown) {
    super(typeof detail === 'string' ? detail : 'Cognix API request failed');
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const authHeaders: Record<string, string> = {};
  if (supabase) {
    const { data } = await supabase.auth.getSession();
    const token = data.session?.access_token;
    if (token) authHeaders.Authorization = `Bearer ${token}`;
  }

  const apiPath = path === '/health' || path === '/ready' || path.startsWith('/v1/') ? path : `${API_PREFIX}${path}`;
  const response = await fetch(`${API_BASE_URL}${apiPath}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
      ...authHeaders,
      ...(init?.headers || {}),
    },
    cache: 'no-store',
  });

  const body = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, body?.detail ?? body ?? response.statusText);
  return body as T;
}

export function getApiBaseUrl() { return API_BASE_URL; }
export function postApi<T>(path: string, body: unknown) {
  return request<T>(path, { method: 'POST', body: JSON.stringify(body) });
}
export function listSources() { return request<{ total: number; items: ApiSource[] }>('/sources'); }
export function getSource(sourceId: string) { return request<ApiSource>(`/sources/${sourceId}`); }
export function createSource(url: string, note?: string) { return request<{ status: string; source: ApiSource }>('/sources', { method: 'POST', body: JSON.stringify({ url, note: note || null }) }); }
export function updateSourceTranslation(sourceId: string, humanEditedMyanmar: string) {
  return request<ApiSource>(`/sources/${sourceId}/translation`, {
    method: 'PATCH',
    body: JSON.stringify({ human_edited_myanmar: humanEditedMyanmar }),
  });
}
export function listProcessing() { return request<{ total: number; items: ApiProcessingTask[] }>('/processing'); }
export function getProcessingTask(taskId: string) { return request<ApiProcessingTask>(`/processing/${taskId}`); }
export function createProcessingTask(sourceId: string) { return request<ApiProcessingTask>('/processing', { method: 'POST', body: JSON.stringify({ source_id: sourceId }) }); }
export function advanceProcessingTask(taskId: string) { return request<ApiProcessingTask>(`/processing/${taskId}/advance`, { method: 'POST' }); }
export function retryProcessingTask(taskId: string) { return request<ApiProcessingTask>(`/processing/${taskId}/retry`, { method: 'POST' }); }
export function approveSource(sourceId: string, note?: string) { return request<{ source_id: string; status: string; note?: string | null }>(`/reviews/${sourceId}/approve`, { method: 'POST', body: JSON.stringify({ note: note || null }) }); }
export function requestSourceRevision(sourceId: string, note?: string) { return request<{ source_id: string; status: string; note?: string | null }>(`/reviews/${sourceId}/revision`, { method: 'POST', body: JSON.stringify({ note: note || null }) }); }
export function exportToGoogleDrive(sourceId: string, idempotencyKey: string) { return request<ApiExportJob>('/exports/google-drive', { method: 'POST', body: JSON.stringify({ source_id: sourceId, idempotency_key: idempotencyKey }) }); }
export function listExports() { return request<{ total: number; items: ApiExportJob[] }>('/exports'); }
export function getExport(exportId: string) { return request<ApiExportJob>(`/exports/${exportId}`); }
export function advanceExport(exportId: string) { return request<ApiExportJob>(`/exports/${exportId}/advance`, { method: 'POST' }); }
export function retryExport(exportId: string) { return request<ApiExportJob>(`/exports/${exportId}/retry`, { method: 'POST' }); }
export function getActivity() { return request<{ total: number; items: Record<string, unknown>[] }>('/activity'); }
export function getUsage() { return request<ApiUsage>('/usage'); }
export function getReady() { return request<{ status: string; persistence_mode: string; database_configured: boolean; database_reachable: boolean }>('/ready'); }

const sourceStatuses = new Set<SourceStatus>(['new', 'processing', 'needs_review', 'approved', 'delivered', 'failed', 'outdated']);
const trustLevels = new Set<TrustLevel>(['verified', 'high', 'medium', 'low', 'unverified']);

function asSourceStatus(value: string): SourceStatus {
  return sourceStatuses.has(value as SourceStatus) ? value as SourceStatus : 'new';
}
function asTrustLevel(value: string | undefined): TrustLevel {
  return trustLevels.has(value as TrustLevel) ? value as TrustLevel : 'unverified';
}

export function apiSourceToSource(source: ApiSource): Source {
  const hostname = (() => { try { return new URL(source.url).hostname; } catch { return source.url; } })();
  const claims = (source.claims || []).map((claim) => ({
    id: claim.id,
    text: claim.text,
    excerpt: claim.excerpt || '',
    location: claim.location || 'Source',
    confidence: claim.confidence === 'high' ? 100 : claim.confidence === 'medium' ? 70 : claim.confidence === 'low' ? 40 : claim.confidence === 'conflicted' ? 20 : 0,
    verification: claim.verification_state === 'needs_verification' ? 'pending' as const : claim.verification_state === 'conflicted' ? 'conflicted' as const : claim.verification_state === 'unsupported' ? 'unsupported' as const : 'verified' as const,
  }));
  const type: SourceType = 'article';
  const summary = source.ai_summary || source.note || '';
  return {
    id: source.id,
    title: source.note || source.url,
    type,
    publisher: hostname,
    author: 'Unknown',
    topic: 'Unclassified',
    status: asSourceStatus(source.status),
    trust: asTrustLevel(source.source_trust),
    priority: source.critical_warnings.length ? 'high' : 'normal',
    url: source.url,
    publishedDate: source.created_at,
    retrievedDate: source.created_at,
    lastProcessed: source.updated_at,
    lastReviewed: source.status === 'approved' ? source.updated_at : null,
    freshness: source.updated_at,
    addedDate: source.created_at,
    version: 'live',
    contentHash: '',
    summary,
    originalText: source.original_text || undefined,
    myanmarTranslation: source.myanmar_translation || undefined,
    humanEditedMyanmar: source.human_edited_myanmar || undefined,
    approvedMyanmar: source.approved_myanmar || undefined,
    keyPoints: source.key_points || [],
    tags: [],
    claims,
    relatedSourceIds: [],
  };
}

export function mergeSources(live: ApiSource[]): Source[] { return live.map(apiSourceToSource); }


export interface ApiBrainBook {
  id: string;
  title: string;
  author?: string | null;
  language: string;
  file_type: string;
  source_kind: string;
  source_url?: string | null;
  status: string;
  description?: string | null;
  category?: string | null;
  content_hash?: string | null;
  created_at: string;
  updated_at: string;
  chunk_count: number;
  chapters?: ApiBrainChapter[];
}
export interface ApiBrainChapter {
  id: string;
  book_id: string;
  chapter_number: number;
  title: string;
  created_at: string;
  chunks?: ApiBrainChunk[];
}
export interface ApiBrainChunk {
  id: string;
  chapter_id: string;
  sequence: number;
  content: string;
  page_number?: number | null;
  token_count?: number | null;
}
export interface ApiBrainNote {
  id: string;
  title: string;
  content: string;
  note_type: string;
  status: string;
  created_at: string;
  updated_at: string;
  sources?: Array<{ source_type: string; source_id: string }>;
}
export interface ApiBrainConcept {
  id: string;
  name: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}
export interface ApiBrainSearchResult {
  book_id?: string;
  book_title?: string;
  chapter_id: string;
  chapter_title: string;
  chunk_id: string;
  sequence: number;
  score: number;
  content: string;
}

export function listBrainBooks() {
  return request<{ total: number; items: ApiBrainBook[] }>('/brain/books');
}
export function getBrainBook(bookId: string) {
  return request<ApiBrainBook>(`/brain/books/${bookId}`);
}
export function createBrainBook(payload: {
  title: string;
  author?: string;
  language?: string;
  file_type?: string;
  description?: string;
  category?: string;
  text: string;
}) {
  return request<ApiBrainBook>('/brain/books', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
export function searchBrainBook(bookId: string, q: string) {
  return request<{ query: string; total: number; items: ApiBrainSearchResult[] }>(
    `/brain/books/${bookId}/search?q=${encodeURIComponent(q)}`,
  );
}
export function listBrainNotes() {
  return request<{ total: number; items: ApiBrainNote[] }>('/brain/notes');
}
export function createBrainNote(payload: {
  title: string;
  content: string;
  note_type?: string;
  status?: string;
  source_type?: string;
  source_id?: string;
}) {
  return request<ApiBrainNote>('/brain/notes', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
export function listBrainConcepts() {
  return request<{ total: number; items: ApiBrainConcept[] }>('/brain/concepts');
}
export function createBrainConcept(payload: { name: string; description?: string }) {
  return request<ApiBrainConcept>('/brain/concepts', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
export function getBrainGraph() {
  return request<{ nodes: ApiBrainConcept[]; edges: Array<Record<string, unknown>> }>('/brain/graph');
}
export function createBrainConceptLink(payload: { from_concept_id: string; to_concept_id: string; relation?: string; weight?: number }) {
  return request<Record<string, unknown>>('/brain/concept-links', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}
export function getNoteBacklinks(noteId: string) {
  return request<{ items: ApiBrainNote[]; total: number }>('/brain/notes/' + noteId + '/backlinks');
}
export function queryBrain(q: string) {
  return request<{ query: string; mode: string; answer: string | null; message: string; total: number; items: ApiBrainSearchResult[] }>(
    `/brain/query?q=${encodeURIComponent(q)}`,
  );
}


export function uploadBrainBook(file: File, language = 'en', description?: string, category = 'Unclassified') {
  const body = new FormData();
  body.append('file', file);
  body.append('language', language);
  if (description) body.append('description', description);
  body.append('category', category);
  return request<ApiBookUploadResponse>('/brain/books/upload', { method: 'POST', body });
}

export interface ApiBookUploadResponse { id: string; status: string; processing_stage: string; content_hash: string; idempotent: boolean; duplicate_of?: string; book: ApiBrainBook; }
export interface ApiBookProgress { book_id: string; stage: string; status: string; completed_units: number; total_units: number; percent: number; current_chapter_id?: string | null; current_chapter_number?: number | null; last_checkpoint_at?: string | null; paused_reason?: string | null; }
export function getBookProgress(bookId: string) { return request<ApiBookProgress>(`/brain/books/${bookId}/progress`); }
export function getBookTimeline(bookId: string) { return request<{items: Array<Record<string, unknown>>; total: number}>(`/brain/books/${bookId}/timeline`); }
export function listKnowledge(category?: string, bookId?: string) { const q = new URLSearchParams(); if (category) q.set('category',category); if (bookId) q.set('book_id',bookId); return request<{items: Array<Record<string, unknown>>; total: number}>(`/brain/knowledge?${q.toString()}`); }
export function listLessonPacks() { return request<{items: Array<Record<string, unknown>>; total: number}>('/brain/lessons'); }
export function listDerivedBooks() { return request<{items: Array<Record<string, unknown>>; total: number}>('/brain/derived-books'); }
export function semanticBrainQuery(q: string, limit = 8) {
  return request<{
    query: string;
    mode: string;
    answer: string | null;
    citations: string[];
    message: string;
    total: number;
    items: Array<{
      chunk_id: string;
      content: string;
      semantic_similarity: number | null;
      semantic_rank: number | null;
      lexical_rank: number | null;
      rrf_score: number;
      chapter_id: string;
      page_number?: number | null;
      sequence: number;
      model?: string | null;
    }>;
  }>('/brain/query/semantic', {
    method: 'POST',
    body: JSON.stringify({ q, limit }),
  });
}


export interface ApiLanguageCard {
  id: string; front: string; back: string; language: string; source_note?: string | null;
  due_at: string; stability: number; difficulty: number; reps: number; lapses: number; state: string;
}
export function getDueLanguageCards(limit = 20) {
  return request<{ items: ApiLanguageCard[]; total: number }>(`/brain/language/due?limit=${limit}`);
}
export function createLanguageCard(payload: { front: string; back: string; language: string; source_note?: string }) {
  return request<ApiLanguageCard>('/brain/language/cards', { method: 'POST', body: JSON.stringify(payload) });
}
export function reviewLanguageCard(cardId: string, rating: 1 | 2 | 3 | 4) {
  return request<ApiLanguageCard>(`/brain/language/cards/${cardId}/review`, { method: 'POST', body: JSON.stringify({ rating }) });
}
export function listBookSummaries(bookId: string) { return request<{items: Array<{id:string;level:string;title?:string|null;content:string;version:number;model?:string|null}>;total:number}>(`/brain/books/${bookId}/summaries`); }
export function generateBookSummaries(bookId: string, levels = ['L1','L2','L3','L4','L5','L6','L7']) {
  return request<{ book_id: string; model: string; items: Array<{ id: string; level: string; version: number; content: string; source_ids: string[] }> }>(
    `/brain/books/${bookId}/summaries/generate`, { method: 'POST', body: JSON.stringify({ levels }) },
  );
}
export function ocrDocument(file: File, language = 'eng', maxPages = 50) {
  const body = new FormData(); body.append('file', file); body.append('language', language); body.append('max_pages', String(maxPages));
  return request<{ job_id: string; status: string; text: string; pages: Array<{ page_number: number; text: string }> }>('/brain/documents/ocr', { method: 'POST', body });
}
export interface ApiVaultItem {
  id: string; label: string; ciphertext?: string; nonce: string; kdf_salt: string; kdf_params: Record<string, unknown>; created_at: string; updated_at: string;
}
export function listVaultItems() { return request<{ items: ApiVaultItem[]; total: number }>('/brain/vault/items'); }
export function getVaultItem(itemId: string) { return request<ApiVaultItem & { ciphertext: string }>(`/brain/vault/items/${encodeURIComponent(itemId)}`); }
export function saveVaultItem(payload: { label: string; ciphertext: string; nonce: string; kdf_salt: string; kdf_params: Record<string, unknown> }) {
  return request<ApiVaultItem>('/brain/vault/items', { method: 'POST', body: JSON.stringify(payload) });
}
export function exportBrainVault() { return request<Record<string, unknown>>('/brain/export'); }

export function ingestBrainMedia(file: File, ocrLanguage = 'eng') {
  const body = new FormData();
  body.append('file', file);
  body.append('ocr_language', ocrLanguage);
  return request<{ id: string; filename: string; media_type: string; content_hash: string; ocr_text: string; message: string }>(
    '/brain/media/ingest',
    { method: 'POST', body },
  );
}
