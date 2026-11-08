'use client';

import { FormEvent, useEffect, useState } from 'react';
import Link from 'next/link';
import { BookOpen, Plus } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { ApiBrainBook, createBrainBook, listBrainBooks, uploadBrainBook } from '@/lib/api';

export default function BooksPage() {
  const [books, setBooks] = useState<ApiBrainBook[]>([]);
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [files, setFiles] = useState<File[]>([]);
  const [category, setCategory] = useState('Unclassified');
  const [notice, setNotice] = useState('');

  const load = async () => setBooks((await listBrainBooks()).items);
  useEffect(() => { load().catch(() => setError('Unable to load the book library.')); }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!title.trim() || !text.trim()) return;
    setSaving(true);
    setError('');
    try {
      await createBrainBook({ title: title.trim(), text: text.trim(), file_type: 'text', category });
      setTitle('');
      setText('');
      await load();
    } catch {
      setError('Book could not be imported.');
    } finally {
      setSaving(false);
    }
  };

  const upload = async () => {
    if (files.length === 0) return;
    setSaving(true);
    setError('');
    try {
      let count = 0;
      for (const f of files) {
        await uploadBrainBook(f, 'en', undefined, category);
        count++;
      }
      setNotice(count > 1 ? `${count} books queued for background AI reading.` : 'Book queued for background AI reading.');
      setFiles([]);
      await load();
    } catch {
      setError('Book upload failed. Make sure persistent book storage is configured.');
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
                    <p className="mt-1 text-xs text-muted-foreground">{book.category || 'Unclassified'} · {book.chunk_count} chunks · {book.language} · {book.processing_stage || book.status}</p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </SectionCard>
        <SectionCard title="Import book" description="Upload a PDF, EPUB, DOCX or TXT (single or multiple). Cognix reads it in the background; you do not need to keep this page open.">
          <form onSubmit={submit} className="space-y-4">
            <select aria-label="Book category" value={category} onChange={(e) => setCategory(e.target.value)} className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"><option>Unclassified</option><option>Business, Entrepreneurship & Finance</option><option>Communication & Negotiation</option><option>Creativity & Tech</option><option>Future Tech</option><option>Leadership & Management</option><option>Productivity, Habits & Discipline</option><option>Psychology & Critical Thinking</option><option>Self-Help & Emotional Intelligence</option><option>Stoicism & Philosophy</option></select>
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Book title (for manual text paste)" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
            <input
              type="file"
              multiple
              accept=".pdf,.epub,.docx,.txt,application/pdf,application/epub+zip,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
              onChange={(e) => setFiles(Array.from(e.target.files || []))}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
            />
            {files.length > 1 && (
              <p className="text-xs text-muted-foreground">
                📚 {files.length} books selected for bulk intake
              </p>
            )}
            <button
              type="button"
              onClick={() => files.length > 0 && upload()}
              disabled={files.length === 0 || saving}
              className="w-full rounded-md border border-border px-4 py-2 text-sm font-medium disabled:opacity-50"
            >
              {saving ? "Uploading…" : files.length > 1 ? `Upload ${files.length} Books (Bulk)` : "Upload Book"}
            </button>
            <div className="text-center text-xs text-muted-foreground">or paste extracted text</div>
            <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste extracted book text here…" rows={10} className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
            {notice && <p className="text-sm text-primary" role="status">{notice}</p>}
            {error && <p className="text-sm text-destructive">{error}</p>}
            <button disabled={saving} className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"><Plus className="h-4 w-4" /> {saving ? 'Importing…' : 'Import book'}</button>
          </form>
        </SectionCard>
      </div>
    </AppShell>
  );
}
