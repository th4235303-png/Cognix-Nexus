import { apiRequest } from './client';
import type { SourceSummary } from '@/lib/types/research';

export function listSources() {
  return apiRequest<{ items: SourceSummary[]; total: number }>('/sources');
}

export function getSource(id: string) {
  return apiRequest<SourceSummary>(`/sources/${id}`);
}

export function createSource(url: string, note?: string) {
  return apiRequest<{ status: string }>('/sources', {
    method: 'POST',
    body: JSON.stringify({ url, note }),
  });
}
