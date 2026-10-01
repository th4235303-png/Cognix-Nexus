'use client';

import { useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { ingestBrainMedia } from '@/lib/api';

export default function LensPage() {
  const [file,setFile]=useState<File|null>(null); const [language,setLanguage]=useState('eng'); const [text,setText]=useState(''); const [error,setError]=useState(''); const [busy,setBusy]=useState(false);
  const run=async()=>{if(!file)return;setBusy(true);setError('');try{const r=await ingestBrainMedia(file,language);setText(r.ocr_text);}catch(e){setError(e instanceof Error?e.message:'Media ingestion failed');}finally{setBusy(false);}};
  return <AppShell><PageHeader title="Vizora Lens" description="Media intelligence input boundary for images entering the Brain Vault." />
    <SectionCard title="Image ingest" description="The current boundary performs OCR and records content hashes. Rich visual understanding remains provider-configured."><div className="space-y-4">
      <input type="file" accept=".png,.jpg,.jpeg,.webp,.tiff,.bmp" onChange={e=>setFile(e.target.files?.[0]||null)} className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
      <input value={language} onChange={e=>setLanguage(e.target.value)} placeholder="Tesseract language, e.g. eng" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
      <button disabled={!file||busy} onClick={run} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">{busy?'Processing…':'Ingest image'}</button>
      {error&&<p className="text-sm text-destructive">{error}</p>}<textarea value={text} onChange={e=>setText(e.target.value)} rows={18} placeholder="OCR / media text will appear here…" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm font-mono" />
    </div></SectionCard></AppShell>;
}
