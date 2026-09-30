'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { RotateCcw, Play, Languages, AlertTriangle, Loader2 } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard, FilterChip } from '@/components/shared/cognix-primitives';
import { stageLabels, type ProcessingStage } from '@/lib/researchData';
import { StageBadge } from '@/components/research/workspace-ui';
import { listProcessing, advanceProcessingTask, retryProcessingTask, type ApiProcessingTask } from '@/lib/api';

const stages: ProcessingStage[] = ['queued','extracting','cleaning','translating','summarizing','key_points','fact_check','trust_scoring','needs_review','approved','failed'];

export default function ProcessingPage() {
  const [filter, setFilter] = useState('all');
  const [rows, setRows] = useState<ApiProcessingTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => { listProcessing().then(r => setRows(r.items)).catch(() => setError('Backend is not available yet; start FastAPI on localhost:8000.')).finally(() => setLoading(false)); }, []);
  async function advance(taskId: string) { setBusy(taskId); setError(null); try { const next = await advanceProcessingTask(taskId); setRows(current => current.map(t => t.id === taskId ? next : t)); } catch { setError('Could not advance this task.'); } finally { setBusy(null); } }
  async function retry(taskId: string) { setBusy(taskId); setError(null); try { const next = await retryProcessingTask(taskId); setRows(current => current.map(t => t.id === taskId ? next : t)); } catch { setError('Could not retry this task.'); } finally { setBusy(null); } }
  const filtered = filter === 'all' ? rows : rows.filter(r => r.stage === filter);
  return <AppShell><PageHeader title="Processing Queue" description="Track extraction, cleaning, translation, summarization, fact-check flags, and approval readiness." action={<span className="inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1.5 text-[11px] text-primary"><Languages className="h-3.5 w-3.5" /> Translation stage enabled</span>} />
    <div className="mb-5 flex flex-wrap gap-2">{['all', ...stages].map(s => <FilterChip key={s} label={s === 'all' ? 'All' : stageLabels[s as ProcessingStage]} active={filter === s} onClick={() => setFilter(s)} count={s === 'all' ? rows.length : rows.filter(r => r.stage === s).length} />)}</div>
    {error && <div className="mb-4 rounded-md border border-warning/25 bg-warning/5 p-3 text-xs text-warning">{error}</div>}
    <SectionCard title="Pipeline tasks" description="Live tasks from the FastAPI processing API.">
      {loading ? <div className="flex items-center gap-2 p-5 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Loading tasks…</div> :
      rows.length === 0 ? <div className="p-5 text-sm text-muted-foreground">No processing tasks yet. Add a source to create one.</div> :
      <div className="space-y-3">{filtered.map(task => { const stage = (task.stage === 'failed' ? 'failed' : task.stage) as ProcessingStage; return <div key={task.id} className="rounded-lg border border-border/40 bg-background-surface/30 p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center"><div className="min-w-0 flex-1"><Link href={`/sources/${task.source_id}`} className="text-sm font-medium hover:text-primary">{task.source_id}</Link><p className="mt-1 font-mono-tight text-[10px] text-muted-foreground">{task.id} · retry {task.retry_count}</p></div><StageBadge stage={stage} /><span className="w-12 text-right font-mono-tight text-xs text-primary">{task.progress}%</span><div className="flex gap-1.5">{task.status === 'completed' ? null : <button disabled={busy === task.id} onClick={() => advance(task.id)} className="rounded-md border border-border/50 p-2 text-muted-foreground hover:text-primary disabled:opacity-40" aria-label="Advance"><Play className="h-3.5 w-3.5" /></button>}<button disabled={busy === task.id} onClick={() => retry(task.id)} className="rounded-md border border-border/50 p-2 text-muted-foreground hover:text-primary disabled:opacity-40" aria-label="Retry"><RotateCcw className="h-3.5 w-3.5" /></button></div></div>
        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary transition-all" style={{width: `${task.progress}%`}} /></div>
        {task.error && <div className="mt-3 flex gap-2 rounded-md border border-destructive/20 bg-destructive/5 p-3 text-xs text-destructive"><AlertTriangle className="h-4 w-4 shrink-0" />{task.error}</div>}
        {task.stage === 'translating' && <p className="mt-2 flex items-center gap-1.5 text-[11px] text-primary"><Languages className="h-3.5 w-3.5 animate-pulse" /> Myanmar translation is being generated. Human editing follows.</p>}
      </div>})}</div>}
    </SectionCard>
  </AppShell>;
}
