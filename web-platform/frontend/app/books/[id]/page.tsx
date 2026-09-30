'use client';

import { FormEvent, useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ArrowLeft, Search } from 'lucide-react';
import Link from 'next/link';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { ApiBrainBook, ApiBrainSearchResult, getBrainBook, searchBrainBook } from '@/lib/api';

export default function BookDetailPage() {
  const params = useParams<{ id: string }>();
  const [book, setBook] = useState<ApiBrainBook | null>(null);
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<ApiBrainSearchResult[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!params.id) return;
    getBrainBook(params.id).then(setBook).catch(() => setError('Book not found.'));
  }, [params.id]);

  const search = async (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;
    try {
      const response = await searchBrainBook(params.id, query);
      setResults(response.items);
    } catch {
      setError('Search failed.');
    }
  };

  if (!book) return <AppShell><PageHeader title="Book Reader" description={error || 'Loading…'} /></AppShell>;

  return (
    <AppShell>
      <div className="mb-4"><Link href="/books" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="h-4 w-4" /> Book Library</Link></div>
      <PageHeader title={book.title} description={(book.author || 'Unknown author') + ' · ' + book.chunk_count + ' chunks'} />
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <SectionCard title="Reader" description="Content is preserved as ordered chapters and chunks.">
          <div className="space-y-6">
            {book.chapters?.map((chapter) => (
              <section key={chapter.id}>
                <h2 className="mb-3 text-lg font-semibold">{chapter.chapter_number}. {chapter.title}</h2>
                <div className="space-y-4">
                  {chapter.chunks?.map((chunk) => <article key={chunk.id} className="rounded-lg border border-border/50 bg-background/30 p-4"><p className="whitespace-pre-wrap text-sm leading-7 text-foreground/90">{chunk.content}</p></article>)}
                </div>
              </section>
            ))}
          </div>
        </SectionCard>
        <SectionCard title="Book search" description="Evidence-ranked text retrieval; semantic embeddings come next.">
          <form onSubmit={search} className="flex gap-2">
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search this book…" className="min-w-0 flex-1 rounded-md border border-border bg-background px-3 py-2 text-sm" />
            <button className="rounded-md border border-border px-3 py-2 hover:bg-white/[0.03]"><Search className="h-4 w-4" /></button>
          </form>
          <div className="mt-4 space-y-3">
            {results.map((result) => <div key={result.chunk_id} className="rounded-lg border border-border/50 p-3"><div className="mb-1 text-xs text-muted-foreground">{result.chapter_title} · score {result.score}</div><p className="text-sm leading-6">{result.content}</p></div>)}
            {!results.length && <p className="text-xs text-muted-foreground">Search results will appear here.</p>}
          </div>
        </SectionCard>
      </div>
    </AppShell>
  );
}
