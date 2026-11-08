'use client';

import { useCallback, useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { ApiBrainConcept, createBrainConcept, createBrainConceptLink, getBrainGraph } from '@/lib/api';

type GraphEdge = { from_concept_id?: string; to_concept_id?: string; source?: string; target?: string; relationship?: string };

export default function GraphPage() {
  const [concepts, setConcepts] = useState<ApiBrainConcept[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [name, setName] = useState('');
  const [from, setFrom] = useState('');
  const [to, setTo] = useState('');
  const [selectedConceptId, setSelectedConceptId] = useState<string | null>(null);
  const [query, setQuery] = useState('');

  const load = useCallback(async () => {
    const graph = await getBrainGraph();
    setConcepts(graph.nodes);
    setEdges(graph.edges as GraphEdge[]);
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

  const visibleConcepts = concepts.filter((concept) => concept.name.toLowerCase().includes(query.trim().toLowerCase()));
  const selectedConcept = concepts.find((concept) => concept.id === selectedConceptId) ?? null;
  const relatedEdges = selectedConcept ? edges.filter((edge) => {
    const source = edge.from_concept_id ?? edge.source;
    const target = edge.to_concept_id ?? edge.target;
    return source === selectedConcept.id || target === selectedConcept.id;
  }) : [];
  const relatedConceptIds = new Set(relatedEdges.flatMap((edge) => [edge.from_concept_id ?? edge.source, edge.to_concept_id ?? edge.target]).filter(Boolean));

  return (
    <AppShell>
      <PageHeader title="Knowledge Graph" description="Concepts and explicit relationships form the second-brain graph." />
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <SectionCard title="Interactive concepts" description={concepts.length + ' concepts · ' + edges.length + ' relationships'}>
          <div className="mb-4 flex flex-wrap items-center gap-2">
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filter graph concepts" className="min-w-[180px] flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm" aria-label="Filter graph concepts" />
            {selectedConcept && <button onClick={() => setSelectedConceptId(null)} className="rounded-md border border-border px-3 py-2 text-sm">Clear focus</button>}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {visibleConcepts.map((concept) => {
              const isSelected = concept.id === selectedConceptId;
              const isRelated = Boolean(selectedConceptId && relatedConceptIds.has(concept.id));
              return <button key={concept.id} onClick={() => setSelectedConceptId(concept.id)} className={`rounded-lg border p-4 text-left transition ${isSelected ? 'border-primary bg-primary/10 ring-1 ring-primary' : isRelated ? 'border-primary/50 bg-primary/5' : 'border-border/50 hover:border-primary/40'}`} aria-pressed={isSelected}>
                <p className="font-medium">{concept.name}</p><p className="mt-1 text-xs text-muted-foreground">{concept.description || 'No description yet.'}</p>
                <p className="mt-3 text-[11px] text-primary">{edges.filter((edge) => (edge.from_concept_id ?? edge.source) === concept.id || (edge.to_concept_id ?? edge.target) === concept.id).length} linked concept(s)</p>
              </button>;
            })}
            {!concepts.length && <p className="text-sm text-muted-foreground">Create a concept to start the graph.</p>}
          </div>
          {selectedConcept && <div className="mt-5 rounded-lg border border-border/60 bg-background/40 p-4" aria-live="polite">
            <p className="font-medium">Focused: {selectedConcept.name}</p>
            <p className="mt-1 text-sm text-muted-foreground">{selectedConcept.description || 'No description yet.'}</p>
            <ul className="mt-3 space-y-1 text-sm text-muted-foreground">
              {relatedEdges.length ? relatedEdges.map((edge, index) => {
                const source = concepts.find((concept) => concept.id === (edge.from_concept_id ?? edge.source))?.name ?? 'Unknown';
                const target = concepts.find((concept) => concept.id === (edge.to_concept_id ?? edge.target))?.name ?? 'Unknown';
                return <li key={`${source}-${target}-${index}`}>{source} → {target}{edge.relationship ? ` (${edge.relationship})` : ''}</li>;
              }) : <li>No relationships yet. Use the link form to connect this concept.</li>}
            </ul>
          </div>}
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
