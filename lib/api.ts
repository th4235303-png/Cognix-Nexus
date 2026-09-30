import { supabase } from '@/lib/supabase';

const API_BASE_URL = (process.env.NEXT_PUBLIC_COGNIX_API_URL || 'http://localhost:8000').replace(/\/$/, '');

import type { Source, SourceStatus, SourceType, TrustLevel } from '@/lib/mockData';

export interface ApiClaim { id: string; text: string; excerpt?: string | null; location?: string | null; confidence: string; verification_state: string; created_at: string; }
export interface ApiSource { id: string; url: string; note?: string | null; status: string; processing_stage: string; created_at: string; updated_at: string; critical_warnings: string[]; claims?: ApiClaim[]; source_trust?: string; original_text?: string | null; ai_summary?: string | null; myanmar_translation?: string | null; human_edited_myanmar?: string | null; approved_myanmar?: string | null; key_points?: string[]; }
export interface ApiProcessingTask { id: string; source_id: string; stage: string; progress: number; status: string; retry_count: number; error: string | null; }
export interface ApiExportJob { id: string; source_id: string; status: string; idempotency_key: string; drive_reference: string | null; files: string[]; }
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

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
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

export function mergeSources(live: ApiSource[], fallback: Source[]): Source[] {
  const liveSources = live.map(apiSourceToSource);
  const liveIds = new Set(liveSources.map((source) => source.id));
  return [...liveSources, ...fallback.filter((source) => !liveIds.has(source.id))];
}
