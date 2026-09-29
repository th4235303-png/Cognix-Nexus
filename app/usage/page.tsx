'use client';

import { useEffect, useState, type ComponentType } from 'react';
import { Cpu, HardDrive, Languages, ListChecks } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { getUsage } from '@/lib/api';

type Usage = { ai_requests_today: number; processing_jobs: number; translation_requests: number; drive_exports: number };

export default function UsagePage() {
  const [usage, setUsage] = useState<Usage>({ ai_requests_today: 0, processing_jobs: 0, translation_requests: 0, drive_exports: 0 });
  useEffect(() => { getUsage().then(setUsage).catch(() => undefined); }, []);

  return <AppShell><PageHeader title="Usage & Limits" description="Live backend usage counters for the current prototype." /><div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4"><Metric label="AI requests today" value={usage.ai_requests_today} limit={1000} icon={Cpu} /><Metric label="Processing jobs" value={usage.processing_jobs} limit={100} icon={ListChecks} /><Metric label="Translation requests" value={usage.translation_requests} limit={500} icon={Languages} /><Metric label="Drive exports" value={usage.drive_exports} limit={100} icon={HardDrive} /></div><div className="mt-6 grid gap-6 lg:grid-cols-2"><SectionCard title="Storage"><p className="text-3xl font-semibold font-mono-tight">Prototype</p><p className="mt-2 text-xs text-muted-foreground">Persistent storage metering will be connected when the production database is enabled.</p></SectionCard><SectionCard title="Metering notes"><ul className="space-y-2 text-sm text-muted-foreground"><li>• Translation requests currently reflect processing tasks at the translation stage.</li><li>• Drive exports count export jobs, including retryable jobs.</li><li>• Failed jobs retain retry history for audit.</li></ul></SectionCard></div></AppShell>;
}
function Metric({label,value,limit,icon:Icon}:{label:string;value:number;limit:number;icon:ComponentType<{className?: string}>}){const pct=Math.min(100,value/limit*100);return <div className="surface-elevated rounded-xl p-5"><Icon className="h-5 w-5 text-primary"/><p className="mt-4 font-mono-tight text-2xl font-semibold">{value.toLocaleString()}</p><p className="text-xs text-muted-foreground">{label} / {limit.toLocaleString()}</p><div className="mt-3 h-1.5 rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{width:`${pct}%`}} /></div></div>}
