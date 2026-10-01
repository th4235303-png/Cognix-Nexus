'use client';

import { useMemo, useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard, GlowButton } from '@/components/shared/cognix-primitives';
import { postApi } from '@/lib/api';

const features = [
  ['4.1','Agent Mode'],['4.2','Synthesis Engine'],['4.3','Decision Support'],['4.4','Writing Assistant'],
  ['4.5','Feynman Mode'],['4.6','Knowledge Decay'],['4.7','Interleaving'],['4.8','Learning Path'],
  ['4.9','Knowledge Gap'],['4.10','Research Mode'],['4.11','Personal Timeline'],['4.12','Mood-Aware'],
  ['4.13','Ambient Learning'],['4.14','Context Restoration'],['4.15','Time Capsule'],['4.16','Personal Wiki'],
  ['4.17','Knowledge Compounding'],['4.18','Idea Generator'],['4.19','Offline-first AI'],['4.20','Legacy Mode'],
];

async function call<T>(path: string, body: unknown) { return postApi<T>(path, body); }

export default function LevelUpPage() {
  const [explanation,setExplanation]=useState('');
  const [feynman,setFeynman]=useState<Record<string,unknown>|null>(null);
  const [subjects,setSubjects]=useState('math,history');
  const [sequence,setSequence]=useState<string[]>([]);
  const [error,setError]=useState<string|null>(null);
  const featureCount = useMemo(()=>features.length,[features]);

  async function runFeynman() {
    setError(null);
    try { setFeynman(await call('/brain/level-up/feynman',{topic:'My topic',explanation,required_terms:[]})); }
    catch(e){setError(e instanceof Error?e.message:'Request failed');}
  }
  async function runInterleave() {
    setError(null);
    try { const r=await call('/brain/level-up/interleave',{subjects:subjects.split(',').map(s=>s.trim()).filter(Boolean),rounds:3}); setSequence(r.sequence); }
    catch(e){setError(e instanceof Error?e.message:'Request failed');}
  }

  return <AppShell>
    <PageHeader title="Level Up 20" description={`${featureCount} feature contracts with evidence, privacy, learning and recovery guardrails.`} />
    {error && <div role="alert" className="mb-5 rounded-lg border border-destructive/30 bg-destructive/5 p-3 text-sm text-destructive">{error}</div>}
    <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
      {features.map(([id,name])=><SectionCard key={id} title={`${id} · ${name}`}><p className="text-xs text-muted-foreground">Available through the Level Up API boundary; source/review constraints remain explicit.</p></SectionCard>)}
    </div>
    <div className="mt-6 grid gap-6 lg:grid-cols-2">
      <SectionCard title="Feynman Mode" description="Explain a topic, then inspect the deterministic mastery signal.">
        <textarea value={explanation} onChange={e=>setExplanation(e.target.value)} placeholder="Explain the idea in your own words…" className="min-h-32 w-full rounded-lg border border-border/50 bg-background p-3 text-sm outline-none focus:border-primary" />
        <div className="mt-3 flex items-center gap-3"><GlowButton onClick={runFeynman} disabled={!explanation.trim()}>Check explanation</GlowButton>{feynman&&<span className="text-sm">Score: <strong>{String(feynman.score)}</strong> · {feynman.mastered?'Mastered':'Needs another pass'}</span>}</div>
      </SectionCard>
      <SectionCard title="Interleaving" description="Build alternating practice from two or more subjects.">
        <input value={subjects} onChange={e=>setSubjects(e.target.value)} className="w-full rounded-lg border border-border/50 bg-background p-3 text-sm outline-none focus:border-primary" />
        <div className="mt-3 flex items-center gap-3"><GlowButton onClick={runInterleave}>Generate sequence</GlowButton><span className="text-xs text-muted-foreground">{sequence.join(' → ')}</span></div>
      </SectionCard>
    </div>
  </AppShell>;
}
