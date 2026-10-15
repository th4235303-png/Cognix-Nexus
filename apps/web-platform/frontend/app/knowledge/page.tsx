'use client';

import { useEffect, useState } from 'react';
import { Download, CheckCircle2, XCircle, BookOpen, Sparkles } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import {
  ApiKnowledgeItem,
  ApiKnowledgeStats,
  exportKnowledge,
  generateDerivedBook,
  generateLessonPack,
  getKnowledgeStats,
  listKnowledge,
  listLessonPacks,
  reviewKnowledge,
} from '@/lib/api';

const categories = [
  'All',
  'Business, Entrepreneurship & Finance',
  'Communication & Negotiation',
  'Creativity & Tech',
  'Future Tech',
  'Leadership & Management',
  'Productivity, Habits & Discipline',
  'Psychology & Critical Thinking',
  'Self-Help & Emotional Intelligence',
  'Stoicism & Philosophy',
];

export default function KnowledgeVaultPage() {
  const [items, setItems] = useState<ApiKnowledgeItem[]>([]);
  const [stats, setStats] = useState<ApiKnowledgeStats | null>(null);
  const [category, setCategory] = useState('All');
  const [status, setStatus] = useState('draft');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState('');
  const [lessonTitle, setLessonTitle] = useState('');
  const [lessonTopic, setLessonTopic] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const [knowledge, summary] = await Promise.all([
        listKnowledge(category === 'All' ? undefined : category, undefined, status),
        getKnowledgeStats(),
      ]);
      setItems(knowledge.items);
      setStats(summary);
    } catch {
      setMessage('Knowledge Vault could not be loaded.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [category, status]);

  const changeReview = async (id: string, next: 'canonical' | 'rejected') => {
    setBusy(id);
    setMessage('');
    try {
      await reviewKnowledge(id, next);
      await load();
      setMessage(next === 'canonical' ? 'Promoted to canonical knowledge.' : 'Marked as rejected.');
    } catch {
      setMessage('Review action failed.');
    } finally {
      setBusy('');
    }
  };

  const downloadExport = async () => {
    setBusy('export');
    try {
      const result = await exportKnowledge('canonical', category === 'All' ? undefined : category);
      const blob = new Blob([result.markdown], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = 'cognix-knowledge-vault.md';
      anchor.click();
      URL.revokeObjectURL(url);
    } catch {
      setMessage('Knowledge export failed.');
    } finally {
      setBusy('');
    }
  };

  const generateLesson = async (derived = false) => {
    if (!lessonTitle.trim()) return;
    setBusy(derived ? 'derived' : 'lesson');
    try {
      const payload = {
        title: lessonTitle.trim(),
        category: category === 'All' ? undefined : category,
        topic: lessonTopic.trim() || undefined,
      };
      const result = derived ? await generateDerivedBook(payload) : await generateLessonPack(payload);
      setMessage((derived ? 'Derived book' : 'Lesson pack') + ' created from ' + String((result.source_book_ids as string[] | undefined)?.length ?? 0) + ' source books.');
    } catch {
      setMessage('Synthesis needs configured AI and at least one matching knowledge item.');
    } finally {
      setBusy('');
    }
  };

  return (
    <AppShell>
      <PageHeader
        title="Knowledge Vault"
        description="Review AI-distilled knowledge, promote trusted items, and synthesize cross-book learning without losing source lineage."
      />
      <div className="grid gap-4 md:grid-cols-4">
        <Metric label="Total" value={stats?.total ?? 0} />
        <Metric label="Draft review" value={stats?.draft ?? 0} />
        <Metric label="Canonical" value={stats?.canonical ?? 0} />
        <Metric label="Rejected" value={stats?.rejected ?? 0} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_340px]">
        <SectionCard title="Distilled knowledge" description="AI output remains draft until you explicitly promote it.">
          <div className="mb-4 flex flex-col gap-3 sm:flex-row">
            <select aria-label="Knowledge category" value={category} onChange={(e) => setCategory(e.target.value)} className="min-w-0 flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm">
              {categories.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
            <select aria-label="Knowledge status" value={status} onChange={(e) => setStatus(e.target.value)} className="rounded-md border border-border bg-background px-3 py-2 text-sm">
              <option value="draft">Needs review</option>
              <option value="canonical">Canonical</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          {loading ? <p className="text-sm text-muted-foreground">Loading knowledge…</p> : (
            <div className="space-y-3">
              {items.map((item) => (
                <article key={item.id} className="rounded-lg border border-border/50 bg-background/30 p-4">
                  <div className="flex items-start gap-3">
                    <BookOpen className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <h2 className="font-medium">{item.title || item.knowledge_type}</h2>
                        <span className="rounded-full border border-border/50 px-2 py-0.5 text-[10px] uppercase text-muted-foreground">{item.knowledge_type}</span>
                        <span className="text-[10px] text-muted-foreground">{item.category}</span>
                      </div>
                      <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-foreground/90">{item.content}</p>
                      <p className="mt-2 text-[11px] text-muted-foreground">Book {item.book_id} · {item.source_chunk_ids?.length ?? 0} source chunks · {item.model || 'provider pending'}</p>
                    </div>
                  </div>
                  {status === 'draft' && (
                    <div className="mt-3 flex gap-2 border-t border-border/30 pt-3">
                      <button type="button" disabled={busy === item.id} onClick={() => changeReview(item.id, 'canonical')} className="focus-ring inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground disabled:opacity-50"><CheckCircle2 className="h-3.5 w-3.5" /> Promote</button>
                      <button type="button" disabled={busy === item.id} onClick={() => changeReview(item.id, 'rejected')} className="focus-ring inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-xs disabled:opacity-50"><XCircle className="h-3.5 w-3.5" /> Reject</button>
                    </div>
                  )}
                </article>
              ))}
              {!items.length && <div className="rounded-lg border border-dashed border-border/60 p-8 text-center text-sm text-muted-foreground">No items in this review state yet.</div>}
            </div>
          )}
        </SectionCard>

        <div className="space-y-6">
          <SectionCard title="Cross-book synthesis" description="Generate a study artifact from the currently filtered knowledge.">
            <div className="space-y-3">
              <input aria-label="Synthesis title" value={lessonTitle} onChange={(e) => setLessonTitle(e.target.value)} placeholder="e.g. Leadership principles" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
              <input aria-label="Synthesis topic" value={lessonTopic} onChange={(e) => setLessonTopic(e.target.value)} placeholder="Optional topic" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
              <button type="button" disabled={!lessonTitle.trim() || !!busy} onClick={() => generateLesson(false)} className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"><Sparkles className="h-4 w-4" /> Generate lesson pack</button>
              <button type="button" disabled={!lessonTitle.trim() || !!busy} onClick={() => generateLesson(true)} className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-md border border-border px-3 py-2 text-sm disabled:opacity-50"><BookOpen className="h-4 w-4" /> Generate derived book</button>
            </div>
          </SectionCard>

          <SectionCard title="Export" description="Download canonical knowledge with source IDs preserved.">
            <button type="button" disabled={busy === 'export'} onClick={downloadExport} className="focus-ring inline-flex w-full items-center justify-center gap-2 rounded-md border border-border px-3 py-2 text-sm disabled:opacity-50"><Download className="h-4 w-4" /> Export Markdown</button>
          </SectionCard>

          {message && <p role="status" className="rounded-md border border-border/50 bg-background/50 p-3 text-xs text-muted-foreground">{message}</p>}
        </div>
      </div>
    </AppShell>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="rounded-lg border border-border/50 bg-background/30 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 text-2xl font-semibold">{value}</p></div>;
}
