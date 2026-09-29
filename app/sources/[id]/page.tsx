'use client';

import { useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { getResearchRecord, type ResearchRecord } from '@/lib/researchData';
import type { Source } from '@/lib/mockData';
import { getSource, type ApiClaim, type ApiSource } from '@/lib/api';
import { ResearchDetail } from '@/components/research/workspace-ui';

const sourceTrustValues: ResearchRecord['sourceTrust'][] = [
  'official', 'primary', 'reputable', 'expert', 'community', 'unverified',
];

function mapClaim(claim: ApiClaim): ResearchRecord['source']['claims'][number] {
  const verification =
    claim.verification_state === 'needs_verification' ? 'pending' : claim.verification_state;
  const confidence =
    claim.confidence === 'high' ? 95 :
    claim.confidence === 'medium' ? 75 :
    claim.confidence === 'low' ? 45 : 20;
  return {
    id: claim.id,
    text: claim.text,
    excerpt: claim.excerpt ?? '',
    location: claim.location ?? '',
    verification: verification as 'verified' | 'pending' | 'unsupported' | 'conflicted',
    confidence,
  };
}

function buildLiveRecord(source: ApiSource, fallback: ResearchRecord | undefined): ResearchRecord {
  const sourceTrust = sourceTrustValues.includes(source.source_trust as ResearchRecord['sourceTrust'])
    ? source.source_trust as ResearchRecord['sourceTrust']
    : fallback?.sourceTrust ?? 'unverified';
  const claims = source.claims?.map(mapClaim) ?? fallback?.source.claims ?? [];
  const sourceRecord: Source = fallback?.source
    ? {
        ...fallback.source,
        id: source.id,
        url: source.url,
        status: source.status as Source['status'],
        claims,
        summary: source.ai_summary ?? fallback.originalSummary,
        originalText: source.original_text ?? fallback.originalText,
        myanmarTranslation: source.myanmar_translation ?? fallback.myanmarTranslation,
        humanEditedMyanmar: source.human_edited_myanmar ?? fallback.humanEditedMyanmar,
        approvedMyanmar: source.approved_myanmar ?? fallback.approvedMyanmar,
      }
    : {
        id: source.id,
        title: source.url,
        type: 'article',
        publisher: new URL(source.url).hostname,
        author: 'Unknown',
        topic: 'Unclassified',
        status: source.status as Source['status'],
        trust: 'unverified',
        priority: 'normal',
        url: source.url,
        publishedDate: source.created_at.slice(0, 10),
        retrievedDate: source.created_at.slice(0, 10),
        lastProcessed: source.updated_at,
        lastReviewed: null,
        freshness: 'Live API source',
        addedDate: source.created_at.slice(0, 10),
        version: 'live',
        contentHash: '',
        summary: source.ai_summary ?? '',
        originalText: source.original_text ?? '',
        myanmarTranslation: source.myanmar_translation ?? '',
        humanEditedMyanmar: source.human_edited_myanmar ?? '',
        approvedMyanmar: source.approved_myanmar ?? '',
        keyPoints: [],
        tags: [],
        claims,
        relatedSourceIds: [],
      };

  const critical = source.critical_warnings.length > 0 || claims.some((claim) =>
    claim.verification === 'conflicted' || claim.verification === 'unsupported');
  return {
    source: sourceRecord,
    originalText: source.original_text ?? fallback?.originalText ?? 'Awaiting source extraction.',
    originalSummary: source.ai_summary ?? fallback?.originalSummary ?? 'No summary yet.',
    myanmarTranslation: source.myanmar_translation ?? fallback?.myanmarTranslation ?? '',
    humanEditedMyanmar: source.human_edited_myanmar ?? fallback?.humanEditedMyanmar ?? '',
    approvedMyanmar: source.approved_myanmar ?? fallback?.approvedMyanmar ?? '',
    processingStage: source.processing_stage as ResearchRecord['processingStage'],
    processingProgress: source.status === 'approved' ? 100 : fallback?.processingProgress ?? 0,
    translationStatus: source.approved_myanmar ? 'approved' : source.human_edited_myanmar ? 'edited' : source.myanmar_translation ? 'ready' : 'pending',
    claimFlags: claims.map((claim) => ({
      id: claim.id,
      type: claim.verification === 'verified' ? 'verified_from_source' :
        claim.verification === 'pending' ? 'needs_verification' :
        claim.verification === 'conflicted' ? 'conflicting_evidence' : 'unsupported_claim',
      label: claim.verification === 'verified' ? 'Verified from source' :
        claim.verification === 'pending' ? 'Needs verification' :
        claim.verification === 'conflicted' ? 'Conflicting evidence' : 'Unsupported claim',
      note: claim.excerpt || 'Evidence requires review.',
      severity: claim.verification === 'conflicted' || claim.verification === 'unsupported' ? 'critical' :
        claim.verification === 'pending' ? 'warning' : 'info',
    })),
    sourceTrust,
    claimConfidence: critical ? 'conflicted' : claims.some((claim) => claim.verification === 'pending') ? 'medium' : claims.length ? 'high' : 'medium',
    exportStatus: source.status === 'approved' || source.status === 'delivered' ? 'ready' : 'not_ready',
    driveReference: null,
    logixaStatus: 'not_sent',
    processingVersion: fallback?.processingVersion ?? 'live',
  };
}

export default function SourceDetailPage({ params }: { params: { id: string } }) {
  const fallback = getResearchRecord(params.id);
  const [record, setRecord] = useState<ResearchRecord | null>(fallback ?? null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    let active = true;
    getSource(params.id)
      .then((live) => {
        if (!active) return;
        setRecord(buildLiveRecord(live, fallback));
        setNotFound(false);
      })
      .catch(() => {
        if (!active) return;
        setNotFound(!fallback);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [params.id, fallback]);

  if (notFound) return <AppShell><div className="p-6 text-sm text-muted-foreground">Source not found.</div></AppShell>;
  return <AppShell>
    {loading && <div className="mb-4 rounded-lg border border-border/40 bg-background-surface/40 p-3 text-xs text-muted-foreground">Loading live source state…</div>}
    {record && <ResearchDetail record={record} />}
  </AppShell>;
}
