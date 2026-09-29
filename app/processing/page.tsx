'use client';

import { useState } from 'react';
import Link from 'next/link';
import { RotateCcw, Pause, Play, Languages, Search, AlertTriangle } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard, FilterChip } from '@/components/shared/cognix-primitives';
import { processingRows, stageLabels, type ProcessingStage } from '@/lib/researchData';
import { StageBadge } from '@/components/research/workspace-ui';

const stages: ProcessingStage[] = ['queued','extracting','cleaning','translating','summarizing','key_points','fact_check','trust_scoring','needs_review','approved','failed'];

export default function ProcessingPage() {
  const [filter, setFilter] = useState('all');
  const rows = processingRows.map((row, i) => i === 0 ? { ...row, stage: 'translating' as ProcessingStage, progress: 72 } : row);
  const filtered = filter === 'all' ? rows : rows.filter(r => r.stage === filter);
  return <AppShell><PageHeader title="Processing Queue" description="Track extraction, cleaning, translation, summarization, fact-check flags, and approval readiness." action={<span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1.5 text-[11px] text-primary"><Languages className="h-3.5 w-3.5" /> Translation stage enabled</span>} />
    <div className="mb-5 flex flex-wrap gap-2">{['all', ...stages].map(s => <FilterChip key={s} label={s === 'all' ? 'All' : stageLabels[s as ProcessingStage]} active={filter === s} onClick={() => setFilter(s)} count={s === 'all' ? rows.length : rows.filter(r => r.stage === s).length} />)}</div>
    <SectionCard title="Pipeline tasks" description="Prototype lifecycle mirrors the planned FastAPI task model.">
      <div className="space-y-3">{filtered.map(task => <div key={task.id} className="rounded-lg border border-border/40 bg-background-surface/30 p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center"><div className="min-w-0 flex-1"><Link href={`/sources/${task.sourceId}`} className="text-sm font-medium hover:text-primary">{task.sourceTitle}</Link><p className="mt-1 font-mono-tight text-[10px] text-muted-foreground">{task.id} · {task.sourceId} · retry {task.retryCount}</p></div><StageBadge stage={task.stage} /><span className="w-12 text-right font-mono-tight text-xs text-primary">{task.progress}%</span><div className="flex gap-1.5"><button className="rounded-md border border-border/50 p-2 text-muted-foreground hover:text-primary" aria-label="Pause"><Pause className="h-3.5 w-3.5" /></button><button className="rounded-md border border-border/50 p-2 text-muted-foreground hover:text-primary" aria-label="Retry"><RotateCcw className="h-3.5 w-3.5" /></button></div></div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary transition-all" style={{width: `${task.progress}%`}} /></div>
        {task.stage === 'failed' && <div className="mt-3 flex gap-2 rounded-md border border-destructive/20 bg-destructive/5 p-3 text-xs text-destructive"><AlertTriangle className="h-4 w-4 shrink-0" />{task.error}</div>}
        {task.stage === 'translating' && <p className="mt-2 flex items-center gap-1.5 text-[11px] text-primary"><Languages className="h-3.5 w-3.5 animate-pulse" /> Myanmar translation is being generated. Human editing follows.</p>}
      </div>)}</div>
    </SectionCard>
  </AppShell>;
}
