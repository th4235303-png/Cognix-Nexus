import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { activityLog } from '@/lib/researchData';
import { HardDrive } from 'lucide-react';

export default function ActivityPage() {
  const rows = [...activityLog, { id:'ACT-9822', user:'System', avatar:'SY', action:'queued Drive export', target:'SRC-0462', previousState:'approved', newState:'export_queued', timestamp:'2026-08-31 09:12:44 UTC', requestId:'req_mock_drive_001' }];
  return <AppShell><PageHeader title="Activity Log" description="Audit trail for processing, review, approval, delivery, and export events." /><SectionCard title="Recent events"><div className="space-y-1">{rows.map(e => <div key={e.id} className="flex gap-3 rounded-md border-b border-border/30 px-2 py-3 last:border-0"><div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-[10px] text-muted-foreground">{e.avatar}</div><div className="min-w-0 flex-1"><p className="text-sm"><span className="font-medium">{e.user}</span> <span className="text-muted-foreground">{e.action}</span> <span className="font-mono-tight text-primary">{e.target}</span></p><p className="mt-1 text-[10px] text-muted-foreground">{e.timestamp} · {e.requestId}</p></div>{e.action.includes('Drive') && <HardDrive className="h-4 w-4 text-primary" />}</div>)}</div></SectionCard></AppShell>;
}
