'use client';

import Link from 'next/link';
import { Suspense, useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Plus, FileText, FileCheck, Video, Mic, Database, Search, Clock, Loader2 } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, GlowButton, FilterChip, EmptyState } from '@/components/shared/cognix-primitives';
import { StatusBadge, TrustBadge, PriorityFlag } from '@/components/shared/status-badges';
import type { SourceType, SourceStatus } from '@/lib/types/source';
import { listSources, mergeSources } from '@/lib/api';

const typeIcons: Record<SourceType, typeof FileText> = { article: FileText, report: FileCheck, paper: FileText, video: Video, podcast: Mic, dataset: Database };
const filters: { label: string; status?: SourceStatus; key: string }[] = [
  { label: 'All', key: 'all' }, { label: 'New', status: 'new', key: 'new' }, { label: 'Processing', status: 'processing', key: 'processing' },
  { label: 'Needs Review', status: 'needs_review', key: 'needs_review' }, { label: 'Approved', status: 'approved', key: 'approved' },
  { label: 'Delivered', status: 'delivered', key: 'delivered' }, { label: 'Failed', status: 'failed', key: 'failed' }, { label: 'Outdated', status: 'outdated', key: 'outdated' },
  { label: 'High Priority', key: 'high_priority' },
];

function AllSourcesContent() {
  const searchParams = useSearchParams();
  const initialSearch = searchParams.get('search') || '';
  const [activeFilter, setActiveFilter] = useState('all');
  const [search, setSearch] = useState(initialSearch);
  const [items, setItems] = useState<ReturnType<typeof mergeSources>>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listSources().then(({ items }) => setItems(mergeSources(items))).catch(() => undefined).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => items.filter((s) => {
    const filterEntry = filters.find((f) => f.key === activeFilter);
    const matchesFilter = activeFilter === 'all' || (activeFilter === 'high_priority' ? s.priority === 'critical' || s.priority === 'high' : s.status === filterEntry?.status);
    const query = search.toLowerCase();
    const matchesSearch = !query || s.title.toLowerCase().includes(query) || s.publisher.toLowerCase().includes(query) || s.topic.toLowerCase().includes(query) || s.tags.some((t) => t.toLowerCase().includes(query));
    return matchesFilter && matchesSearch;
  }), [activeFilter, items, search]);

  return <AppShell>
    <PageHeader title="All Sources" description="Complete library of ingested research sources across all statuses." action={<Link href="/sources/add"><GlowButton><Plus className="h-4 w-4" /> Add Source</GlowButton></Link>} />
    <div className="mb-4 flex flex-wrap items-center gap-2">{filters.map((f) => {
      const count = f.key === 'all' ? items.length : f.key === 'high_priority' ? items.filter((s) => s.priority === 'critical' || s.priority === 'high').length : items.filter((s) => s.status === f.status).length;
      return <FilterChip key={f.key} label={f.label} active={activeFilter === f.key} onClick={() => setActiveFilter(f.key)} count={count} />;
    })}</div>
    <div className="relative mb-4"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/50" /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by title, publisher, topic, or tag..." className="h-10 w-full rounded-lg border border-border/50 bg-background-elevated pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground/50 focus-glow focus:outline-none transition-all" /></div>
    {loading ? <div className="flex items-center justify-center rounded-xl border border-border/40 p-10 text-sm text-muted-foreground"><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading live sources…</div> : filtered.length === 0 ? <EmptyState icon={FileText} title="No sources found" description="Try adjusting your filters or search terms." action={<Link href="/sources/add"><GlowButton><Plus className="h-4 w-4" /> Add Source</GlowButton></Link>} /> : <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{filtered.map((source) => {
      const Icon = typeIcons[source.type];
      return <Link key={source.id} href={`/sources/${source.id}`} className="group surface-elevated rounded-xl p-4 transition-all duration-300 hover:border-border/80 hover:-translate-y-0.5">
        <div className="flex items-start justify-between gap-2"><div className="flex items-center gap-2"><div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 border border-primary/20"><Icon className="h-4 w-4 text-primary" /></div><span className="font-mono-tight text-[10px] text-muted-foreground">{source.id}</span></div><StatusBadge status={source.status} /></div>
        <h3 className="mt-3 text-sm font-medium leading-snug text-foreground group-hover:text-primary transition-colors">{source.title}</h3>
        <p className="mt-1 text-xs text-muted-foreground">{source.publisher} · {source.author}</p>
        {source.summary && <p className="mt-2 text-xs text-muted-foreground/80 line-clamp-2">{source.summary}</p>}
        <div className="mt-3 flex items-center gap-2 flex-wrap border-t border-border/30 pt-3"><TrustBadge trust={source.trust} /><PriorityFlag priority={source.priority} /><span className="ml-auto flex items-center gap-1 text-[11px] text-muted-foreground font-mono-tight"><Clock className="h-3 w-3" /> {source.freshness}</span></div>
        <div className="mt-2 flex flex-wrap gap-1">{source.tags.slice(0, 3).map((tag) => <span key={tag} className="rounded-full bg-muted/40 border border-border/30 px-2 py-0.5 text-[10px] text-muted-foreground">{tag}</span>)}</div>
      </Link>;
    })}</div>}
  </AppShell>;
}

export default function AllSourcesPage() {
  return (
    <Suspense fallback={<AppShell><div className="flex items-center justify-center rounded-xl border border-border/40 p-10 text-sm text-muted-foreground">Loading sources…</div></AppShell>}>
      <AllSourcesContent />
    </Suspense>
  );
}
