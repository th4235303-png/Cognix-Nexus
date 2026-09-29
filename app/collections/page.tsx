import { FolderOpen } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { collections } from '@/lib/mockData';

export default function CollectionsPage(){return <AppShell><PageHeader title="Collections" description="Organize approved and in-progress research into durable knowledge groups." /><div className="grid gap-4 md:grid-cols-2">{collections.map(c=><SectionCard key={c.id} title={c.name} description={c.description} action={<FolderOpen className="h-4 w-4 text-primary"/>}><div className="flex items-center justify-between text-xs text-muted-foreground"><span>{c.sourceCount} sources</span><span>Updated {c.updatedAt}</span></div></SectionCard>)}</div></AppShell>}
