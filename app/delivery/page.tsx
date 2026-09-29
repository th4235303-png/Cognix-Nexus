'use client';

import { useEffect, useState } from 'react';
import { HardDrive } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { deliveryEvents, exportRows } from '@/lib/researchData';
import { listExports, listSources, retryExport, type ApiExportJob, type ApiSource } from '@/lib/api';

export default function DeliveryPage() {
  const [liveExports, setLiveExports] = useState<ApiExportJob[]>([]);
  const [sourceMap, setSourceMap] = useState<Record<string, ApiSource>>({});
  const [retrying, setRetrying] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([listExports(), listSources()])
      .then(([exportsResponse, sourcesResponse]) => {
        setLiveExports(exportsResponse.items);
        setSourceMap(Object.fromEntries(sourcesResponse.items.map(source => [source.id, source])));
      })
      .catch(() => undefined);
  }, []);

  async function retry(id: string) {
    setRetrying(id);
    try {
      const updated = await retryExport(id);
      setLiveExports(rows => rows.map(row => row.id === id ? updated : row));
    } finally {
      setRetrying(null);
    }
  }

  const driveRows = liveExports.length
    ? liveExports.map(item => ({
        id: item.id,
        sourceId: item.source_id,
        title: sourceMap[item.source_id]?.url || item.source_id,
        exportStatus: item.status,
        driveReference: item.drive_reference,
      }))
    : exportRows;

  return <AppShell>
    <PageHeader title="Delivery Center" description="Separate downstream Logixa Flow delivery from private Google Drive export." />
    <div className="grid gap-6 lg:grid-cols-2">
      <SectionCard title="Logixa Flow delivery" description="Downstream delivery events remain independent from Drive export.">
        <div className="space-y-3">{deliveryEvents.map(e => <div key={e.id} className="rounded-lg border border-border/40 p-4"><div className="flex items-center justify-between gap-3"><div><p className="text-sm font-medium">{e.sourceTitle}</p><p className="mt-1 text-[10px] text-muted-foreground">{e.id} · {e.version}</p></div><span className={`rounded-full border px-2 py-1 text-[10px] ${e.status==='failed'?'border-destructive/25 bg-destructive/10 text-destructive':e.status==='retry_pending'?'border-warning/25 bg-warning/10 text-warning':'border-success/25 bg-success/10 text-success'}`}>{e.status.replace('_',' ')}</span></div><p className="mt-2 text-[11px] text-muted-foreground">{e.destination} · attempts {e.attemptCount}</p>{e.error && <p className="mt-2 text-xs text-destructive">{e.error}</p>}</div>)}</div>
      </SectionCard>
      <SectionCard title="Google Drive export" description="Approved knowledge is packaged and uploaded separately.">
        <div className="space-y-3">
          {driveRows.length === 0 && <div className="rounded-lg border border-border/40 p-5 text-sm text-muted-foreground">No export jobs yet.</div>}
          {driveRows.map(e => <div key={e.id} className="rounded-lg border border-border/40 p-4"><div className="flex items-center justify-between"><div className="flex items-center gap-2"><HardDrive className="h-4 w-4 text-primary" /><p className="text-sm font-medium">{e.title}</p></div><span className="text-[10px] capitalize text-muted-foreground">{e.exportStatus.replace('_',' ')}</span></div><p className="mt-2 font-mono-tight text-[10px] text-muted-foreground">{e.id} · {e.sourceId}</p><div className="mt-3 flex items-center gap-2"><div className="min-w-0 flex-1 rounded-md bg-background-surface p-2 font-mono-tight text-[10px] text-muted-foreground">{e.driveReference || 'No private path exposed'}</div>{['failed','retry_pending'].includes(e.exportStatus) && <button disabled={retrying === e.id} onClick={() => retry(e.id)} className="rounded-md border border-border/50 px-2.5 py-2 text-[10px] hover:border-primary/30 disabled:opacity-50">{retrying === e.id ? 'Retrying…' : 'Retry'}</button>}</div></div>)}
        </div>
      </SectionCard>
    </div>
  </AppShell>;
}
