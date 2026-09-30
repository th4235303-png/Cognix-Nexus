'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { BookOpen, Plus } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { ApiBrainBook, createBrainBook, listBrainBooks } from '@/lib/api';

export default function BooksPage() {
  const [books, setBooks] = useState<ApiBrainBook[]>([]);
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const load = async () => setBooks((await listBrainBooks()).items);
  useEffect(() => { load().catch(() => setError('Unable to load the book library.')); }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!title.trim() || !text.trim()) return;
    setSaving(true);
    setError('');
    try {
      await createBrainBook({ title: title.trim(), text: text.trim(), file_type: 'text' });
      setTitle('');
      setText('');
      await load();
    } catch {
      setError('Book could not be imported.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppShell>
      <PageHeader title="Book Library" description="Your reading layer for the Cognix Brain Vault." />
      <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <SectionCard title="Books" description={books.length + ' books in the vault'}>
          <div className="space-y-3">
            {books.length === 0 && <div className="rounded-lg border border-dashed border-border/60 p-8 text-center text-sm text-muted-foreground">No books yet. Import a text-based book to create the first durable reader record.</div>}
            {books.map((book) => (
              <Link key={book.id} href={'/books/' + book.id} className="block rounded-lg border border-border/60 p-4 hover:border-primary/40 hover:bg-primary/[0.03] transition-colors">
                <div className="flex items-start gap-3">
                  <BookOpen className="mt-0.5 h-5 w-5 text-primary" />
                  <div className="min-w-0">
                    <p className="font-medium text-foreground">{book.title}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{book.author || 'Unknown author'} · {book.chunk_count} chunks · {book.language}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </SectionCard>
        <SectionCard title="Import book" description="Foundation importer. PDF/EPUB adapters can attach to the same model later.">
          <form onSubmit={submit} className="space-y-4">
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Book title" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
            <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste extracted book text here…" rows={10} className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
            {error && <p className="text-sm text-destructive">{error}</p>}
            <button disabled={saving} className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"><Plus className="h-4 w-4" /> {saving ? 'Importing…' : 'Import book'}</button>
          </form>
        </SectionCard>
      </div>
    </AppShell>
  );
}
