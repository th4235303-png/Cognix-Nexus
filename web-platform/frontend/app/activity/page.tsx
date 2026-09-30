'use client';

import { useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { getActivity } from '@/lib/api';
import { HardDrive, RefreshCw } from 'lucide-react';

type ActivityRow = {
  id: string;
  action: string;
  target: string;
  previous_state: string;
  new_state: string;
  timestamp: string;
};

export default function ActivityPage() {
  const [rows, setRows] = useState<ActivityRow[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = () => {
    setLoading(true);
    getActivity().then(({ items }) => setRows(items as ActivityRow[])).catch(() => undefined).finally(() => setLoading(false));
  };

  useEffect(() => { refresh(); }, []);

  return <AppShell><PageHeader title="Activity Log" description="Audit trail for processing, review, approval, delivery, and export events." action={<button onClick={refresh} className="inline-flex items-center gap-2 rounded-md border border-border/50 px-3 py-2 text-xs hover:border-primary/30"><RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh</button>} />
    <SectionCard title="Recent events">
      {loading && rows.length === 0 ? <p className="py-8 text-center text-sm text-muted-foreground">Loading activity…</p> :
      rows.length === 0 ? <p className="py-8 text-center text-sm text-muted-foreground">No activity recorded yet.</p> :
      <div className="space-y-1">{rows.map(e => <div key={e.id} className="flex gap-3 rounded-md border-b border-border/30 px-2 py-3 last:border-0"><div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-[10px] text-muted-foreground">SY</div><div className="min-w-0 flex-1"><p className="text-sm"><span className="font-medium">System</span> <span className="text-muted-foreground">{e.action}</span> <span className="font-mono-tight text-primary">{e.target}</span></p><p className="mt-1 text-[10px] text-muted-foreground">{e.timestamp} · {e.previous_state} → {e.new_state}</p></div>{e.action.includes('drive_export') && <HardDrive className="h-4 w-4 text-primary" />}</div>)}</div>}
    </SectionCard>
  </AppShell>;
}
