'use client';

import { useCallback, useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { ApiBrainConcept, createBrainConcept, createBrainConceptLink, getBrainGraph } from '@/lib/api';

export default function GraphPage() {
  const [concepts, setConcepts] = useState<ApiBrainConcept[]>([]);
  const [edges, setEdges] = useState<Array<Record<string, unknown>>>([]);
  const [name, setName] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');

  const load = useCallback(async () => {
    const graph = await getBrainGraph();
    setConcepts(graph.nodes);
    setEdges(graph.edges);
    if (!from && graph.nodes[0]) setFrom(graph.nodes[0].id);
    if (!to && graph.nodes[1]) setTo(graph.nodes[1].id);
  }, [from, to]);

  useEffect(() => { load().catch(() => undefined); }, [load]);

  const addConcept = async () => {
    if (!name.trim()) return;
    await createBrainConcept({ name: name.trim() });
    setName('');
    await load();
  };

  const link = async () => {
    if (!from || !to || from === to) return;
    await createBrainConceptLink({ from_concept_id: from, to_concept_id: to });
    await load();
  };

  return (
    <AppShell>
      <PageHeader title="Knowledge Graph" description="Concepts and explicit relationships form the second-brain graph." />
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <SectionCard title="Concepts" description={concepts.length + ' concepts · ' + edges.length + ' relationships'}>
          <div className="grid gap-3 sm:grid-cols-2">
            {concepts.map((concept) => <div key={concept.id} className="rounded-lg border border-border/50 p-4"><p className="font-medium">{concept.name}</p><p className="mt-1 text-xs text-muted-foreground">{concept.description || 'No description yet.'}</p></div>)}
            {!concepts.length && <p className="text-sm text-muted-foreground">Create a concept to start the graph.</p>}
          </div>
        </SectionCard>
        <div className="space-y-6">
          <SectionCard title="Add concept">
            <div className="flex gap-2">
              <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Concept name" className="min-w-0 flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm" />
              <button onClick={addConcept} className="rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground">Add</button>
            </div>
          </SectionCard>
          <SectionCard title="Link concepts">
            <div className="space-y-3">
              <select value={from} onChange={(e) => setFrom(e.target.value)} className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                <option value="">From concept</option>{concepts.map((concept) => <option key={concept.id} value={concept.id}>{concept.name}</option>)}
              </select>
              <select value={to} onChange={(e) => setTo(e.target.value)} className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                <option value="">To concept</option>{concepts.map((concept) => <option key={concept.id} value={concept.id}>{concept.name}</option>)}
              </select>
              <button onClick={link} className="w-full rounded-md border border-border px-3 py-2 text-sm hover:bg-white/[0.03]">Create relationship</button>
            </div>
          </SectionCard>
        </div>
      </div>
    </AppShell>
  );
}
