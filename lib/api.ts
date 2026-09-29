const API_BASE_URL = (process.env.NEXT_PUBLIC_COGNIX_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export interface ApiSource {
  id: string;
  url: string;
  note?: string | null;
  status: string;
  processing_stage: string;
  created_at: string;
  updated_at: string;
  critical_warnings: string[];
}

export interface ApiProcessingTask {
  id: string;
  source_id: string;
  stage: string;
  progress: number;
  status: string;
  retry_count: number;
  error: string | null;
}

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
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    cache: 'no-store',
  });

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(response.status, body?.detail ?? body ?? response.statusText);
  }
  return body as T;
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export function createSource(url: string, note?: string) {
  return request<{ status: string; source: ApiSource }>('/sources', {
    method: 'POST',
    body: JSON.stringify({ url, note: note || null }),
  });
}

export function createProcessingTask(sourceId: string) {
  return request<ApiProcessingTask>('/processing', {
    method: 'POST',
    body: JSON.stringify({ source_id: sourceId }),
  });
}

export function advanceProcessingTask(taskId: string) {
  return request<ApiProcessingTask>(`/processing/${taskId}/advance`, { method: 'POST' });
}

export function retryProcessingTask(taskId: string) {
  return request<ApiProcessingTask>(`/processing/${taskId}/retry`, { method: 'POST' });
}

export function approveSource(sourceId: string, note?: string) {
  return request<{ source_id: string; status: string; note?: string | null }>(
    `/reviews/${sourceId}/approve`,
    { method: 'POST', body: JSON.stringify({ note: note || null }) },
  );
}

export function requestSourceRevision(sourceId: string, note?: string) {
  return request<{ source_id: string; status: string; note?: string | null }>(
    `/reviews/${sourceId}/revision`,
    { method: 'POST', body: JSON.stringify({ note: note || null }) },
  );
}

export function exportToGoogleDrive(sourceId: string, idempotencyKey: string) {
  return request<{
    id: string;
    source_id: string;
    status: string;
    drive_reference: string | null;
    files: string[];
  }>('/exports/google-drive', {
    method: 'POST',
    body: JSON.stringify({ source_id: sourceId, idempotency_key: idempotencyKey }),
  });
}
