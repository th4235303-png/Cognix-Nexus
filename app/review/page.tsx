'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { FileText } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { researchRecords } from '@/lib/researchData';
import { listSources } from '@/lib/api';
import { FlagBadge, ReviewGate, StageBadge } from '@/components/research/workspace-ui';

export default function ReviewPage() {
  const [liveStatuses, setLiveStatuses] = useState<Record<string, string>>({});
  useEffect(() => {
    listSources().then(({ items }) => {
      setLiveStatuses(Object.fromEntries(items.map((item) => [item.id, item.status])));
    }).catch(() => undefined);
  }, []);

  const rows = useMemo(() => researchRecords
    .map((record) => {
      const liveStatus = liveStatuses[record.source.id];
      return liveStatus ? { ...record, source: { ...record.source, status: liveStatus as typeof record.source.status } } : record;
    })
    .filter((r) => r.source.status === 'needs_review' || r.claimFlags.some((f) => f.severity === 'critical')), [liveStatuses]);

  return <AppShell><PageHeader title="Review Center" description="Human review is the gate between processed research and approved knowledge." />
    <div className="mb-5 grid gap-3 sm:grid-cols-3"><Stat label="Needs review" value={rows.length} /><Stat label="Critical flags" value={rows.reduce((n,r)=>n+r.claimFlags.filter(f=>f.severity==='critical').length,0)} /><Stat label="Ready to approve" value={rows.filter(r=>!r.claimFlags.some(f=>f.severity==='critical')).length} /></div>
    <div className="space-y-5">{rows.map(record => <SectionCard key={record.source.id} title={record.source.title} description={`${record.source.id} · ${record.source.publisher}`} action={<StageBadge stage="needs_review" />}>
      <div className="grid gap-4 lg:grid-cols-3"><div><p className="text-xs text-muted-foreground">Source trust</p><p className="mt-1 text-sm font-medium capitalize">{record.sourceTrust}</p></div><div><p className="text-xs text-muted-foreground">Claim confidence</p><p className="mt-1 text-sm font-medium capitalize">{record.claimConfidence}</p></div><div><p className="text-xs text-muted-foreground">Translation</p><p className="mt-1 text-sm font-medium capitalize">{record.translationStatus}</p></div></div>
      <div className="mt-4 space-y-2">{record.claimFlags.map(f => <div key={f.id} className="flex items-center justify-between rounded-md border border-border/40 px-3 py-2"><span className="text-xs text-muted-foreground">{f.note}</span><FlagBadge state={f.type === 'conflicting_evidence' ? 'conflicted' : f.type === 'unsupported_claim' ? 'unsupported' : 'needs_verification'} label={f.label} /></div>)}</div>
      <div className="mt-5"><ReviewGate record={record} /></div>
      <Link href={`/sources/${record.source.id}`} className="mt-4 inline-flex items-center gap-2 text-xs text-primary hover:text-primary/80"><FileText className="h-3.5 w-3.5" /> Open full review</Link>
    </SectionCard>)}</div>
  </AppShell>;
}
function Stat({label,value}:{label:string;value:number}){return <div className="surface-elevated rounded-lg p-4"><p className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</p><p className="mt-1 font-mono-tight text-2xl font-semibold">{value}</p></div>}
