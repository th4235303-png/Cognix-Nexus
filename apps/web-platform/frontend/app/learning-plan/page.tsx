'use client';

import { useEffect, useState } from 'react';
import { CheckCircle2, Loader2, RefreshCw, XCircle } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { getLearningPath, listLearningPathItems, persistLearningPath, reviewLearningPathItem, type LearningPathItem } from '@/lib/api';

export default function LearningPlanPage() {
  const [suggested, setSuggested] = useState<LearningPathItem[]>([]);
  const [saved, setSaved] = useState<LearningPathItem[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  const load = async () => {
    setBusy(true); setMessage('');
    try {
      const [path, existing] = await Promise.all([getLearningPath(), listLearningPathItems()]);
      setSuggested(path.items); setSaved(existing.items);
    } catch (error) { setMessage(error instanceof Error ? error.message : 'Unable to load a local learning plan.'); }
    finally { setBusy(false); }
  };
  useEffect(() => { void load(); }, []);

  const save = async () => {
    if (!suggested.length) return;
    setBusy(true); setMessage('');
    try { await persistLearningPath(suggested); setMessage('Daily plan saved with its evidence references.'); await load(); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Unable to save the plan.'); }
    finally { setBusy(false); }
  };
  const review = async (item: LearningPathItem, state: 'active' | 'completed' | 'skipped') => {
    if (!item.id) return;
    setBusy(true); setMessage('');
    try { await reviewLearningPathItem(item.id, state); await load(); }
    catch (error) { setMessage(error instanceof Error ? error.message : 'Unable to update the item.'); }
    finally { setBusy(false); }
  };

  return <AppShell><PageHeader title="Daily Learning Plan" description="A local, evidence-backed review path. It does not call an AI provider." />
    {message && <p className="mb-4 rounded-md border border-border bg-muted/30 p-3 text-sm">{message}</p>}
    <div className="grid gap-6 lg:grid-cols-2">
      <SectionCard title="Suggested next reviews" description="Generated from your recorded learning signals and decay ranking." action={<button onClick={() => void load()} disabled={busy} className="inline-flex items-center gap-1 rounded border border-border px-3 py-1.5 text-xs"><RefreshCw className="h-3.5 w-3.5" /> Refresh</button>}>
        <div className="space-y-3">{suggested.map((item) => <article key={`${item.subject_id}-${item.position}`} className="rounded-md border border-border/60 p-3"><p className="font-medium">{item.position + 1}. {item.subject_id}</p><p className="mt-1 text-sm text-muted-foreground">{item.reason}</p><p className="mt-2 text-xs text-muted-foreground">Evidence: {item.evidence_refs.length} reference(s)</p></article>)}{!suggested.length && !busy && <p className="text-sm text-muted-foreground">Record learning signals with evidence to generate today’s plan.</p>}</div>
        <button onClick={() => void save()} disabled={busy || !suggested.length} className="mt-4 inline-flex items-center gap-2 rounded bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">{busy && <Loader2 className="h-4 w-4 animate-spin" />} Save daily plan</button>
      </SectionCard>
      <SectionCard title="Saved plan" description="Each item is updated explicitly; nothing is marked complete automatically."><div className="space-y-3">{saved.map((item) => <article key={item.id || item.subject_id} className="rounded-md border border-border/60 p-3"><p className="font-medium">{item.position + 1}. {item.subject_id}</p><p className="mt-1 text-sm text-muted-foreground">{item.reason}</p><div className="mt-3 flex gap-2"><button disabled={busy || !item.id} onClick={() => void review(item, 'completed')} className="inline-flex items-center gap-1 rounded border border-success/40 px-2 py-1 text-xs text-success"><CheckCircle2 className="h-3.5 w-3.5" /> Complete</button><button disabled={busy || !item.id} onClick={() => void review(item, 'skipped')} className="inline-flex items-center gap-1 rounded border border-border px-2 py-1 text-xs"><XCircle className="h-3.5 w-3.5" /> Skip</button></div></article>)}{!saved.length && <p className="text-sm text-muted-foreground">No saved plan yet.</p>}</div></SectionCard>
    </div>
  </AppShell>;
}
