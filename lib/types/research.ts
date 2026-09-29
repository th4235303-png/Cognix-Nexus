export type ProcessingStage =
  | 'queued' | 'extracting' | 'cleaning' | 'translating' | 'summarizing'
  | 'key_points' | 'fact_check' | 'trust_scoring' | 'needs_review' | 'approved'
  | 'export_queued' | 'exporting' | 'exported' | 'failed';

export interface SourceSummary {
  id: string;
  title: string;
  url: string;
  status: string;
}

export interface ProcessingTaskDto {
  id: string;
  source_id: string;
  status: string;
  stage: ProcessingStage;
  progress: number;
}

export interface ExportJobDto {
  id: string;
  source_id: string;
  status: string;
  drive_reference?: string | null;
}
