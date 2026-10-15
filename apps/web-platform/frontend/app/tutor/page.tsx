'use client';

import { useEffect, useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { ApiLanguageCard, createLanguageCard, getDueLanguageCards, reviewLanguageCard } from '@/lib/api';

export default function TutorPage() {
  const [cards, setCards] = useState<ApiLanguageCard[]>([]);
  const [front, setFront] = useState(''); const [back, setBack] = useState(''); const [language, setLanguage] = useState('en'); const [error, setError] = useState('');
  const load = async () => setCards((await getDueLanguageCards()).items);
  useEffect(() => { load().catch(() => setError('Unable to load due cards.')); }, []);
  const add = async () => { if (!front.trim() || !back.trim()) return; await createLanguageCard({ front: front.trim(), back: back.trim(), language }); setFront(''); setBack(''); await load(); };
  return <AppShell><PageHeader title="Language Tutor" description="Review due cards with a spaced-repetition schedule." />
    <div className="grid gap-6 lg:grid-cols-[360px_1fr]"><SectionCard title="Create card"><div className="space-y-3">
      <input value={language} onChange={e=>setLanguage(e.target.value)} placeholder="Language" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
      <input value={front} onChange={e=>setFront(e.target.value)} placeholder="Front" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
      <textarea value={back} onChange={e=>setBack(e.target.value)} placeholder="Back / explanation" rows={5} className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
      <button onClick={()=>add().catch(e=>setError(String(e)))} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">Add card</button>
      {error && <p className="text-xs text-destructive">{error}</p>}</div></SectionCard>
      <SectionCard title="Due now" description={cards.length + ' cards'}><div className="space-y-4">
        {cards.map(card => <article key={card.id} className="rounded-lg border border-border/60 p-4"><p className="font-medium">{card.front}</p><p className="mt-2 text-sm text-muted-foreground">{card.back}</p><div className="mt-4 flex flex-wrap gap-2">
          {[1,2,3,4].map(rating => <button key={rating} onClick={()=>reviewLanguageCard(card.id,rating as 1|2|3|4).then(load)} className="rounded-md border border-border px-3 py-1.5 text-xs hover:bg-muted">Rate {rating}</button>)}</div></article>)}
        {!cards.length && <p className="text-sm text-muted-foreground">Nothing due right now.</p>}
      </div></SectionCard></div></AppShell>;
}
