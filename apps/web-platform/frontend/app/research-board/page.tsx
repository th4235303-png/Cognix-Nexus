'use client';

import { ChangeEvent, useEffect, useRef, useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';

type BoardStatus = 'inbox' | 'researching' | 'ready';
type BoardItem = { id: string; title: string; notes: string; status: BoardStatus; createdAt: string };
const STORAGE_KEY = 'cognix-research-board-v1';
const columns: Array<{ status: BoardStatus; label: string }> = [
  { status: 'inbox', label: 'Inbox' }, { status: 'researching', label: 'Researching' }, { status: 'ready', label: 'Ready to apply' },
];

function readBoard(): BoardItem[] {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const value: unknown = raw ? JSON.parse(raw) : [];
    return Array.isArray(value) ? value.filter((item): item is BoardItem => Boolean(item && typeof item.title === 'string' && ['inbox', 'researching', 'ready'].includes(item.status))) : [];
  } catch { return []; }
}

export default function ResearchBoardPage() {
  const [items, setItems] = useState<BoardItem[]>([]);
  const [title, setTitle] = useState('');
  const [notes, setNotes] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => setItems(readBoard()), []);
  useEffect(() => { window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items)); }, [items]);

  const addItem = () => {
    if (!title.trim()) return;
    setItems((current) => [{ id: crypto.randomUUID(), title: title.trim(), notes: notes.trim(), status: 'inbox', createdAt: new Date().toISOString() }, ...current]);
    setTitle(''); setNotes('');
  };
  const move = (id: string, status: BoardStatus) => setItems((current) => current.map((item) => item.id === id ? { ...item, status } : item));
  const remove = (id: string) => setItems((current) => current.filter((item) => item.id !== id));
  const download = () => {
    const blob = new Blob([JSON.stringify({ format: 'cognix-research-board', version: 1, exportedAt: new Date().toISOString(), items }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = 'cognix-research-board.json'; link.click(); URL.revokeObjectURL(url);
  };
  const importBoard = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]; event.target.value = ''; if (!file) return;
    try {
      const parsed: unknown = JSON.parse(await file.text());
      if (!parsed || typeof parsed !== 'object' || !Array.isArray((parsed as { items?: unknown }).items)) throw new Error('Invalid');
      const valid = (parsed as { items: unknown[] }).items.filter((item): item is BoardItem => Boolean(item && typeof (item as BoardItem).id === 'string' && typeof (item as BoardItem).title === 'string' && ['inbox', 'researching', 'ready'].includes((item as BoardItem).status)));
      setItems((current) => [...current, ...valid.filter((candidate) => !current.some((item) => item.id === candidate.id))]);
    } catch { window.alert('This is not a valid Cognix research-board JSON file.'); }
  };

  return <AppShell>
    <PageHeader title="Research & Project Board" description="Local-first planning board. Nothing is sent to another app or service; export/import JSON when you choose." />
    <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
      <SectionCard title="Capture a project">
        <div className="space-y-3">
          <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Research question or project" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" aria-label="Project title" />
          <textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Context, evidence, next step…" className="min-h-28 w-full rounded-md border border-border bg-background px-3 py-2 text-sm" aria-label="Project notes" />
          <button onClick={addItem} className="w-full rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground">Add to inbox</button>
          <div className="flex gap-2 border-t border-border pt-3"><button onClick={download} className="rounded-md border border-border px-3 py-2 text-sm">Export JSON</button><button onClick={() => fileRef.current?.click()} className="rounded-md border border-border px-3 py-2 text-sm">Import JSON</button><input ref={fileRef} type="file" accept="application/json,.json" className="hidden" onChange={importBoard} /></div>
        </div>
      </SectionCard>
      <div className="grid gap-4 md:grid-cols-3">
        {columns.map((column) => <SectionCard key={column.status} title={`${column.label} (${items.filter((item) => item.status === column.status).length})`}>
          <div className="space-y-3">{items.filter((item) => item.status === column.status).map((item) => <article key={item.id} className="rounded-lg border border-border/60 p-3"><p className="font-medium">{item.title}</p>{item.notes && <p className="mt-1 whitespace-pre-wrap text-xs text-muted-foreground">{item.notes}</p>}<div className="mt-3 flex flex-wrap gap-1">{columns.filter((choice) => choice.status !== item.status).map((choice) => <button key={choice.status} onClick={() => move(item.id, choice.status)} className="rounded border border-border px-2 py-1 text-[11px]">Move to {choice.label}</button>)}<button onClick={() => remove(item.id)} className="rounded border border-destructive/40 px-2 py-1 text-[11px] text-destructive">Remove</button></div></article>)}{!items.some((item) => item.status === column.status) && <p className="text-sm text-muted-foreground">No items.</p>}</div>
        </SectionCard>)}
      </div>
    </div>
  </AppShell>;
}
