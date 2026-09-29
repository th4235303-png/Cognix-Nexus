import { Tags } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { tagTopics } from '@/lib/mockData';

export default function TagsPage(){return <AppShell><PageHeader title="Tags & Topics" description="Controlled vocabulary for source discovery, filtering, and future search indexing." /><SectionCard title="Vocabulary"><div className="flex flex-wrap gap-2">{tagTopics.map(t=><span key={t.id} className="inline-flex items-center gap-1.5 rounded-full border border-border/40 bg-background-surface px-3 py-1.5 text-xs"><Tags className="h-3 w-3 text-primary"/>{t.label}<span className="text-muted-foreground">{t.count}</span></span>)}</div></SectionCard></AppShell>}
