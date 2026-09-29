import { HardDrive } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { deliveryEvents } from '@/lib/researchData';
import { exportRows } from '@/lib/researchData';

export default function DeliveryPage() {
  return <AppShell><PageHeader title="Delivery Center" description="Separate downstream Logixa Flow delivery from private Google Drive export." />
    <div className="grid gap-6 lg:grid-cols-2">
      <SectionCard title="Logixa Flow delivery" description="Downstream delivery events remain independent from Drive export.">
        <div className="space-y-3">{deliveryEvents.map(e => <div key={e.id} className="rounded-lg border border-border/40 p-4"><div className="flex items-center justify-between gap-3"><div><p className="text-sm font-medium">{e.sourceTitle}</p><p className="mt-1 text-[10px] text-muted-foreground">{e.id} · {e.version}</p></div><span className={`rounded-full border px-2 py-1 text-[10px] ${e.status==='failed'?'border-destructive/25 bg-destructive/10 text-destructive':e.status==='retry_pending'?'border-warning/25 bg-warning/10 text-warning':'border-success/25 bg-success/10 text-success'}`}>{e.status.replace('_',' ')}</span></div><p className="mt-2 text-[11px] text-muted-foreground">{e.destination} · attempts {e.attemptCount}</p>{e.error && <p className="mt-2 text-xs text-destructive">{e.error}</p>}</div>)}</div>
      </SectionCard>
      <SectionCard title="Google Drive export" description="Approved knowledge is packaged and uploaded separately.">
        <div className="space-y-3">{exportRows.map(e => <div key={e.id} className="rounded-lg border border-border/40 p-4"><div className="flex items-center justify-between"><div className="flex items-center gap-2"><HardDrive className="h-4 w-4 text-primary" /><p className="text-sm font-medium">{e.title}</p></div><span className="text-[10px] capitalize text-muted-foreground">{e.exportStatus.replace('_',' ')}</span></div><p className="mt-2 font-mono-tight text-[10px] text-muted-foreground">{e.id} · {e.sourceId}</p><div className="mt-3 rounded-md bg-background-surface p-2 font-mono-tight text-[10px] text-muted-foreground">{e.driveReference || 'No private path exposed'}</div></div>)}</div>
      </SectionCard>
    </div>
  </AppShell>;
}
