'use client';

import { FormEvent, useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { ApiBrainNote, createBrainNote, listBrainNotes } from '@/lib/api';

export default function NotesPage() {
  const [notes, setNotes] = useState<ApiBrainNote[]>([]);
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const load = async () => setNotes((await listBrainNotes()).items);
  useEffect(() => { load().catch(() => undefined); }, []);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!title.trim() || !content.trim()) return;
    await createBrainNote({ title: title.trim(), content: content.trim() });
    setTitle('');
    setContent('');
    await load();
  };

  return (
    <AppShell>
      <PageHeader title="Second Brain" description="Capture durable notes and grow the knowledge layer." />
      <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
        <SectionCard title="New note">
          <form onSubmit={submit} className="space-y-3">
            <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Note title" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
            <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="Write a durable note…" rows={9} className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
            <button className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Save note</button>
          </form>
        </SectionCard>
        <SectionCard title="Notes" description={notes.length + ' notes'}>
          <div className="space-y-3">
            {notes.map((note) => <article key={note.id} className="rounded-lg border border-border/50 p-4"><h2 className="font-medium">{note.title}</h2><p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-muted-foreground">{note.content}</p></article>)}
            {!notes.length && <p className="text-sm text-muted-foreground">No notes yet.</p>}
          </div>
        </SectionCard>
      </div>
    </AppShell>
  );
}
