'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { CheckCircle2, HardDrive, ExternalLink } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { researchRecords, type ResearchRecord } from '@/lib/researchData';
import { listSources, type ApiSource } from '@/lib/api';
import { ExportButton, StageBadge } from '@/components/research/workspace-ui';

export default function ApprovedPage() {
  const [records, setRecords] = useState<ResearchRecord[]>(researchRecords);
  useEffect(() => {
    listSources().then(({ items }) => {
      if (!items.length) return;
      const liveById = new Map(items.map(source => [source.id, source]));
      setRecords(researchRecords
        .filter(record => liveById.get(record.source.id)?.status === 'approved' || liveById.get(record.source.id)?.status === 'delivered')
        .map(record => {
          const live = liveById.get(record.source.id) as ApiSource;
          return { ...record, source: { ...record.source, status: live.status as ResearchRecord['source']['status'] } };
        }));
    }).catch(() => undefined);
  }, []);
  const approved = records.filter(r => r.source.status === 'approved' || r.source.status === 'delivered');
  return <AppShell><PageHeader title="Approved Knowledge" description="Human-approved research records ready for delivery and Google Drive export." />
    <div className="mb-5 rounded-lg border border-success/20 bg-success/5 p-4 text-xs text-success"><CheckCircle2 className="mr-2 inline h-4 w-4" />Only records that pass the human approval gate should enter this collection.</div>
    <div className="grid gap-4 lg:grid-cols-2">{approved.map(record => <SectionCard key={record.source.id} title={record.source.title} description={`${record.source.id} · ${record.source.publisher}`} action={<StageBadge stage="approved" />}>
      <p className="text-sm leading-6 text-muted-foreground">{record.source.summary}</p>
      <div className="mt-4 flex flex-wrap gap-2">{record.source.tags.map(t => <span key={t} className="rounded-full bg-muted px-2.5 py-1 text-[10px] text-muted-foreground">#{t}</span>)}</div>
      <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-border/30 pt-4"><div className="flex items-center gap-2 text-xs text-muted-foreground"><HardDrive className="h-4 w-4" /> Drive: {record.driveReference || 'Ready to export'}</div><div className="flex gap-2"><Link href={`/sources/${record.source.id}`} className="inline-flex items-center gap-1.5 rounded-md border border-border/50 px-3 py-2 text-xs hover:border-primary/30"><ExternalLink className="h-3.5 w-3.5" /> Details</Link><ExportButton sourceId={record.source.id} status={record.exportStatus === 'exported' ? 'exported' : 'ready'} /></div></div>
    </SectionCard>)}</div>
  </AppShell>;
}
