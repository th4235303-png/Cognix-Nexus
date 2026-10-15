'use client';

import { useEffect, useState } from 'react';
import { HardDrive } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { advanceExport, listExports, listSources, retryExport, type ApiExportJob, type ApiSource } from '@/lib/api';

export default function DeliveryPage() {
  const [liveExports, setLiveExports] = useState<ApiExportJob[]>([]);
  const [sourceMap, setSourceMap] = useState<Record<string, ApiSource>>({});
  const [retrying, setRetrying] = useState<string | null>(null);
  const [advancing, setAdvancing] = useState<string | null>(null);

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

  async function advance(id: string) {
    setAdvancing(id);
    try {
      const updated = await advanceExport(id);
      setLiveExports(rows => rows.map(row => row.id === id ? updated : row));
    } finally {
      setAdvancing(null);
    }
  }

  const driveRows = liveExports.map(item => ({ id: item.id, sourceId: item.source_id, title: sourceMap[item.source_id]?.url || item.source_id, exportStatus: item.status, driveReference: item.drive_reference, error: item.error }));

  return <AppShell>
    <PageHeader title="Google Drive Delivery" description="Approved knowledge is packaged and stored in Google Drive for downstream use." />
    <SectionCard title="Google Drive export" description="Approved knowledge is exported as a structured research package.">
      <div className="space-y-3">
        {driveRows.length === 0 && <div className="rounded-lg border border-border/40 p-5 text-sm text-muted-foreground">No export jobs yet.</div>}
        {driveRows.map(e => <div key={e.id} className="rounded-lg border border-border/40 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2"><HardDrive className="h-4 w-4 text-primary" /><p className="text-sm font-medium">{e.title}</p></div>
            <span className="text-[10px] capitalize text-muted-foreground">{e.exportStatus.replace('_',' ')}</span>
          </div>
          <p className="mt-2 font-mono-tight text-[10px] text-muted-foreground">{e.id} · {e.sourceId}</p>
          <div className="mt-3 flex items-center gap-2">
            <div className="min-w-0 flex-1 rounded-md bg-background-surface p-2 font-mono-tight text-[10px] text-muted-foreground">{e.driveReference || 'Drive upload pending'}</div>
            {['queued','uploading'].includes(e.exportStatus) && <button disabled={advancing === e.id} onClick={() => advance(e.id)} className="rounded-md border border-primary/30 px-2.5 py-2 text-[10px] hover:border-primary/50 disabled:opacity-50">{advancing === e.id ? 'Advancing…' : e.exportStatus === 'queued' ? 'Start upload' : 'Complete upload'}</button>}
            {['failed','retry_pending'].includes(e.exportStatus) && <button disabled={retrying === e.id} onClick={() => retry(e.id)} className="rounded-md border border-border/50 px-2.5 py-2 text-[10px] hover:border-primary/30 disabled:opacity-50">{retrying === e.id ? 'Retrying…' : 'Retry'}</button>}
          </div>
          {e.error && <p className="mt-2 text-xs text-destructive">{e.error}</p>}
        </div>)}
      </div>
    </SectionCard>
  </AppShell>;
}
