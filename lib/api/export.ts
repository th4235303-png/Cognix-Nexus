import { apiRequest } from './client';
import type { ExportJobDto } from '@/lib/types/research';

export function exportToGoogleDrive(sourceId: string, idempotencyKey: string) {
  return apiRequest<ExportJobDto>('/exports/google-drive', {
    method: 'POST',
    body: JSON.stringify({ source_id: sourceId, idempotency_key: idempotencyKey }),
  });
}

export function getExport(id: string) {
  return apiRequest<ExportJobDto>(`/exports/${id}`);
}
