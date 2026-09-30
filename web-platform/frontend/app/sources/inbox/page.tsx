'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { Plus, FileText, FileCheck, Video, Mic, Database, AlertTriangle, Search, Loader2 } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, GlowButton, FilterChip, EmptyState } from '@/components/shared/cognix-primitives';
import { StatusBadge, TrustBadge, PriorityFlag } from '@/components/shared/status-badges';
import { sources as mockSources, type SourceType, type SourceStatus } from '@/lib/mockData';
import { listSources, mergeSources } from '@/lib/api';

const typeIcons: Record<SourceType, typeof FileText> = { article: FileText, report: FileCheck, paper: FileText, video: Video, podcast: Mic, dataset: Database };
const filters: { label: string; status?: SourceStatus; key: string }[] = [
  { label: 'All', key: 'all' }, { label: 'New', status: 'new', key: 'new' }, { label: 'Processing', status: 'processing', key: 'processing' },
  { label: 'Needs Review', status: 'needs_review', key: 'needs_review' }, { label: 'Approved', status: 'approved', key: 'approved' },
  { label: 'Delivered', status: 'delivered', key: 'delivered' }, { label: 'Failed', status: 'failed', key: 'failed' }, { label: 'Outdated', status: 'outdated', key: 'outdated' },
];

export default function SourceInboxPage() {
  const [activeFilter, setActiveFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [items, setItems] = useState(mockSources);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listSources().then(({ items }) => setItems(mergeSources(items, mockSources))).catch(() => undefined).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => items.filter((s) => {
    const matchesFilter = activeFilter === 'all' || s.status === filters.find((f) => f.key === activeFilter)?.status;
    const query = search.toLowerCase();
    return matchesFilter && (!query || s.title.toLowerCase().includes(query) || s.publisher.toLowerCase().includes(query) || s.topic.toLowerCase().includes(query));
  }), [activeFilter, items, search]);
  const duplicateWarning = items.some((s) => s.duplicate);

  return <AppShell>
    <PageHeader title="Source Inbox" description="Newly ingested sources awaiting processing and review." action={<Link href="/sources/add"><GlowButton><Plus className="h-4 w-4" /> Add Source</GlowButton></Link>} />
    {duplicateWarning && <div className="mb-4 flex items-center gap-3 rounded-lg border border-warning/30 bg-warning/5 px-4 py-3"><AlertTriangle className="h-4 w-4 shrink-0 text-warning" /><p className="text-sm text-warning/90">A potential duplicate source was detected. Review before processing to avoid redundancy.</p></div>}
    <div className="mb-4 flex flex-wrap items-center gap-2">{filters.map((f) => {
      const count = f.key === 'all' ? items.length : items.filter((s) => s.status === f.status).length;
      return <FilterChip key={f.key} label={f.label} active={activeFilter === f.key} onClick={() => setActiveFilter(f.key)} count={count} />;
    })}</div>
    <div className="relative mb-4"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/50" /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search by title, publisher, or topic..." className="h-10 w-full rounded-lg border border-border/50 bg-background-elevated pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground/50 focus-glow focus:outline-none transition-all" /></div>
    {loading ? <div className="flex items-center justify-center rounded-xl border border-border/40 p-10 text-sm text-muted-foreground"><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading live sources…</div> : filtered.length === 0 ? <EmptyState icon={FileText} title="No sources found" description="No sources match the current filter. Try adjusting your filters or add a new source." action={<Link href="/sources/add"><GlowButton><Plus className="h-4 w-4" /> Add Source</GlowButton></Link>} /> : <div className="overflow-hidden rounded-xl border border-border/40">
      <table className="w-full"><thead><tr className="border-b border-border/40 bg-background-surface/50">{['Title','Type','Publisher','Status','Trust','Freshness','Priority'].map((label) => <th key={label} className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wider text-muted-foreground">{label}</th>)}</tr></thead>
      <tbody>{filtered.map((source) => { const Icon = typeIcons[source.type]; return <tr key={source.id} className="border-b border-border/30 transition-colors hover:bg-white/[0.02] last:border-0">
        <td className="px-4 py-3"><Link href={`/sources/${source.id}`} className="block max-w-xs truncate text-sm font-medium text-foreground hover:text-primary transition-colors">{source.title}</Link><p className="mt-0.5 font-mono-tight text-[10px] text-muted-foreground">{source.id}</p></td>
        <td className="px-4 py-3"><span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground"><Icon className="h-3.5 w-3.5" />{source.type}</span></td>
        <td className="px-4 py-3 text-xs text-muted-foreground">{source.publisher}</td><td className="px-4 py-3"><StatusBadge status={source.status} /></td><td className="px-4 py-3"><TrustBadge trust={source.trust} /></td><td className="px-4 py-3 text-xs text-muted-foreground font-mono-tight">{source.freshness}</td><td className="px-4 py-3"><PriorityFlag priority={source.priority} /></td>
      </tr>; })}</tbody></table>
    </div>}
  </AppShell>;
}
