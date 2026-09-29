import { apiRequest } from './client';

export function listReviews() {
  return apiRequest<{ items: unknown[]; total: number }>('/reviews');
}

export function approveReview(sourceId: string, note?: string) {
  return apiRequest<{ status: string }>(`/reviews/${sourceId}/approve`, {
    method: 'POST',
    body: JSON.stringify({ note }),
  });
}

export function requestRevision(sourceId: string, note?: string) {
  return apiRequest<{ status: string }>(`/reviews/${sourceId}/revision`, {
    method: 'POST',
    body: JSON.stringify({ note }),
  });
}
