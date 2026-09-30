import { apiRequest } from './client';
import type { ProcessingTaskDto } from '@/lib/types/research';

export function listProcessingTasks() {
  return apiRequest<{ items: ProcessingTaskDto[]; total: number }>('/processing');
}

export function getProcessingTask(id: string) {
  return apiRequest<ProcessingTaskDto>(`/processing/${id}`);
}
