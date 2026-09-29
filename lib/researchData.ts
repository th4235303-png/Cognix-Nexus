import { sources, processingTasks, deliveryEvents, activityLog, usageData, type Source } from '@/lib/mockData';

export type ProcessingStage =
  | 'queued' | 'extracting' | 'cleaning' | 'translating' | 'summarizing'
  | 'key_points' | 'fact_check' | 'trust_scoring' | 'needs_review' | 'approved'
  | 'export_queued' | 'exporting' | 'exported' | 'failed';

export type FlagType =
  | 'verified_from_source' | 'needs_verification' | 'unsupported_claim'
  | 'conflicting_evidence' | 'missing_citation' | 'ambiguous_wording' | 'outdated_information';

export type ClaimState = 'verified' | 'needs_verification' | 'unsupported' | 'conflicted';

export type ExportStatus = 'not_ready' | 'ready' | 'queued' | 'uploading' | 'exported' | 'retry_pending' | 'failed' | 'duplicate_ignored';

export interface ResearchRecord {
  source: Source;
  originalText: string;
  originalSummary: string;
  myanmarTranslation: string;
  humanEditedMyanmar: string;
  approvedMyanmar: string;
  processingStage: ProcessingStage;
  processingProgress: number;
  translationStatus: 'pending' | 'processing' | 'ready' | 'edited' | 'approved';
  claimFlags: Array<{ id: string; type: FlagType; label: string; note: string; severity: 'critical' | 'warning' | 'info' }>;
  sourceTrust: 'official' | 'primary' | 'reputable' | 'expert' | 'community' | 'unverified';
  claimConfidence: 'high' | 'medium' | 'low' | 'conflicted' | 'unsupported';
  exportStatus: ExportStatus;
  driveReference: string | null;
  logixaStatus: 'not_sent' | 'queued' | 'delivered' | 'failed';
  processingVersion: string;
}

const claimFlagLabel: Record<string, { type: FlagType; label: string; note: string; severity: 'critical'|'warning'|'info' }> = {
  verified: { type: 'verified_from_source', label: 'Verified from source', note: 'Claim has a matching source excerpt.', severity: 'info' },
  pending: { type: 'needs_verification', label: 'Needs verification', note: 'Evidence should be checked before approval.', severity: 'warning' },
  conflicted: { type: 'conflicting_evidence', label: 'Conflicting evidence', note: 'Available evidence does not fully agree.', severity: 'critical' },
  unsupported: { type: 'unsupported_claim', label: 'Unsupported claim', note: 'No supporting evidence is currently attached.', severity: 'critical' },
};

function makeRecord(source: Source): ResearchRecord {
  const flags = source.claims.map((claim) => ({
    id: claim.id,
    ...claimFlagLabel[claim.verification],
  }));
  const critical = flags.some((f) => f.severity === 'critical');
  const stage: ProcessingStage =
    source.status === 'approved' || source.status === 'delivered' ? 'approved' :
    source.status === 'needs_review' ? 'needs_review' :
    source.status === 'failed' ? 'failed' :
    source.status === 'processing' ? 'summarizing' : 'queued';
  const progress = source.status === 'processing' ? 64 : source.status === 'needs_review' ? 100 : source.status === 'approved' || source.status === 'delivered' ? 100 : 8;
  const sourceTrust: ResearchRecord['sourceTrust'] =
    source.trust === 'verified' ? 'official' : source.trust === 'high' ? 'primary' : source.trust === 'medium' ? 'reputable' : source.trust === 'low' ? 'community' : 'unverified';
  return {
    source,
    originalText: source.summary ? `Original source content placeholder for “${source.title}”. Full extracted text will come from the FastAPI extraction service.` : 'Awaiting source extraction.',
    originalSummary: source.summary,
    myanmarTranslation: source.summary ? `[Mock Myanmar translation] ${source.summary}` : '',
    humanEditedMyanmar: source.summary ? `[Mock human-edited Myanmar version] ${source.summary}` : '',
    approvedMyanmar: source.status === 'approved' || source.status === 'delivered' ? `[Mock approved Myanmar version] ${source.summary}` : '',
    processingStage: stage,
    processingProgress: progress,
    translationStatus: source.status === 'approved' || source.status === 'delivered' ? 'approved' : source.status === 'needs_review' ? 'edited' : source.status === 'processing' ? 'processing' : 'pending',
    claimFlags: flags,
    sourceTrust,
    claimConfidence: critical ? 'conflicted' : source.claims.some((c) => c.verification === 'pending') ? 'medium' : source.claims.length ? 'high' : 'medium',
    exportStatus: source.status === 'delivered' ? 'exported' : source.status === 'approved' ? 'ready' : 'not_ready',
    driveReference: source.status === 'delivered' ? 'drive://cognix-core/2026-08-11/SRC-0455' : null,
    logixaStatus: source.status === 'delivered' ? 'delivered' : 'not_sent',
    processingVersion: source.version,
  };
}

export const researchRecords: ResearchRecord[] = sources.map(makeRecord);

export function getResearchRecord(id: string) {
  return researchRecords.find((record) => record.source.id === id);
}

export const stageLabels: Record<ProcessingStage, string> = {
  queued: 'Queued',
  extracting: 'Extracting',
  cleaning: 'Cleaning',
  translating: 'Translating',
  summarizing: 'Summarizing',
  key_points: 'Key Points',
  fact_check: 'Fact-check Flagging',
  trust_scoring: 'Trust Scoring',
  needs_review: 'Needs Review',
  approved: 'Approved',
  export_queued: 'Export Queued',
  exporting: 'Exporting',
  exported: 'Drive Exported',
  failed: 'Failed',
};

export const processingRows = processingTasks.map((task) => {
  const stage: ProcessingStage =
    task.status === 'failed' ? 'failed' :
    task.stage === 'extracting' ? 'extracting' :
    task.stage === 'summarizing' ? 'summarizing' :
    task.stage === 'needs_review' ? 'needs_review' :
    task.stage === 'completed' ? 'approved' : 'queued';
  return { ...task, stage };
});

export const exportRows = researchRecords
  .filter((r) => r.exportStatus !== 'not_ready' || r.source.status === 'approved')
  .map((r) => ({
    id: `EXP-${r.source.id.replace('SRC-', '')}`,
    sourceId: r.source.id,
    title: r.source.title,
    exportStatus: r.exportStatus,
    logixaStatus: r.logixaStatus,
    driveReference: r.driveReference,
    updatedAt: r.source.lastReviewed || r.source.retrievedDate,
  }));

export { activityLog, deliveryEvents, usageData };
