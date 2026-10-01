'use client';

import { FormEvent, useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { ApiBrainSearchResult, queryBrain, semanticBrainQuery } from '@/lib/api';

export default function BrainChatPage() {
  const [query, setQuery] = useState('');
  const [items, setItems] = useState<ApiBrainSearchResult[]>([]);
  const [message, setMessage] = useState('Ask across your current Brain Vault evidence.');
  const [loading, setLoading] = useState(false);
  const [semantic, setSemantic] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      if (semantic) {
        const response = await semanticBrainQuery(query.trim());
        setItems(response.items.map((item) => ({ chunk_id: item.chunk_id, chapter_id: item.chapter_id, chapter_title: 'Semantic match', book_title: 'Brain Vault', sequence: item.sequence, score: Number((item.semantic_similarity ?? item.rrf_score).toFixed(4)), content: item.content })));
        setMessage('Semantic retrieval returned cited source chunks.');
      } else {
        const response = await queryBrain(query.trim());
        setItems(response.items);
        setMessage(response.message);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <PageHeader title="Brain Query" description="Search your knowledge base with evidence-first retrieval." />
      <SectionCard title="Online Query">
        <form onSubmit={submit} className="flex flex-wrap gap-2">
          <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="What do I know about…?" className="min-w-0 flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm" />
          <label className="flex items-center gap-2 rounded-md border border-border px-3 text-xs"><input type="checkbox" checked={semantic} onChange={(e) => setSemantic(e.target.checked)} /> Semantic</label>\n          <button disabled={loading} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">{loading ? 'Searching…' : 'Search'}</button>
        </form>
        <p className="mt-3 text-xs text-muted-foreground">{message}</p>
        <div className="mt-5 space-y-3">
          {items.map((item) => <article key={item.chunk_id} className="rounded-lg border border-border/50 p-4"><div className="text-xs text-muted-foreground">{item.book_title} · {item.chapter_title} · score {item.score}</div><p className="mt-2 text-sm leading-6">{item.content}</p></article>)}
        </div>
      </SectionCard>
    </AppShell>
  );
}
