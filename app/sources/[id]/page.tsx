'use client';

import { useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { getResearchRecord, type ResearchRecord } from '@/lib/researchData';
import { getSource, type ApiClaim } from '@/lib/api';
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

export default function SourceDetailPage({ params }: { params: { id: string } }) {
  const fallback = getResearchRecord(params.id);
  const [record, setRecord] = useState<ResearchRecord | null>(fallback ?? null);
  const [loading, setLoading] = useState(Boolean(fallback));

  useEffect(() => {
    let active = true;
    getSource(params.id)
      .then((live) => {
        if (!active || !fallback) return;
        const sourceTrust = sourceTrustValues.includes(live.source_trust as ResearchRecord['sourceTrust'])
          ? live.source_trust as ResearchRecord['sourceTrust']
          : fallback.sourceTrust;
        const liveClaims = live.claims?.map(mapClaim) ?? fallback.source.claims;
        setRecord({
          ...fallback,
          processingStage: live.processing_stage as ResearchRecord['processingStage'],
          sourceTrust,
          originalText: live.original_text ?? fallback.originalText,
          originalSummary: live.ai_summary ?? fallback.originalSummary,
          myanmarTranslation: live.myanmar_translation ?? fallback.myanmarTranslation,
          humanEditedMyanmar: live.human_edited_myanmar ?? fallback.humanEditedMyanmar,
          approvedMyanmar: live.approved_myanmar ?? fallback.approvedMyanmar,
          source: {
            ...fallback.source,
            status: live.status as ResearchRecord['source']['status'],
            claims: liveClaims,
          },
        });
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [params.id, fallback]);

  if (!fallback) return <AppShell><div className="p-6 text-sm text-muted-foreground">Source not found.</div></AppShell>;
  return <AppShell>
    {loading && <div className="mb-4 rounded-lg border border-border/40 bg-background-surface/40 p-3 text-xs text-muted-foreground">Loading live source state…</div>}
    {record && <ResearchDetail record={record} />}
  </AppShell>;
}
