'use client';

import { useEffect, useState } from 'react';
import { notFound } from 'next/navigation';
import { AppShell } from '@/components/layout/app-shell';
import { getResearchRecord, type ResearchRecord } from '@/lib/researchData';
import { getSource } from '@/lib/api';
import { ResearchDetail } from '@/components/research/workspace-ui';

export default function SourceDetailPage({ params }: { params: { id: string } }) {
  const fallback = getResearchRecord(params.id);
  const [record, setRecord] = useState<ResearchRecord | null>(fallback);
  const [loading, setLoading] = useState(Boolean(fallback));

  useEffect(() => {
    let active = true;
    getSource(params.id)
      .then((live) => {
        if (!active || !fallback) return;
        const liveClaims = live.claims ?? fallback.source.claims;
        setRecord({
          ...fallback,
          processingStage: live.processing_stage as ResearchRecord['processingStage'],
          sourceTrust: live.source_trust ?? fallback.sourceTrust,
          originalText: live.original_text ?? fallback.originalText,
          originalSummary: live.ai_summary ?? fallback.originalSummary,
          myanmarTranslation: live.myanmar_translation ?? fallback.myanmarTranslation,
          humanEditedMyanmar: live.human_edited_myanmar ?? fallback.humanEditedMyanmar,
          approvedMyanmar: live.approved_myanmar ?? fallback.approvedMyanmar,
          source: {
            ...fallback.source,
            status: live.status as ResearchRecord['source']['status'],
            claims: liveClaims.map((claim) => ({
              ...claim,
              excerpt: claim.excerpt ?? '',
              location: claim.location ?? '',
              verification: claim.verification_state as 'verified' | 'needs_verification' | 'unsupported' | 'conflicted',
              confidence: claim.confidence === 'high' ? 95 : claim.confidence === 'medium' ? 75 : claim.confidence === 'low' ? 45 : 20,
            })),
          },
          claimFlags: fallback.claimFlags,
        });
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  }, [params.id, fallback]);

  if (!fallback) notFound();
  return <AppShell>
    {loading && <div className="mb-4 rounded-lg border border-border/40 bg-background-surface/40 p-3 text-xs text-muted-foreground">Loading live source state…</div>}
    {record && <ResearchDetail record={record} />}
  </AppShell>;
}
