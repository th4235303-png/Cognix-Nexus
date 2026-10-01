'use client';

import { useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { ocrDocument } from '@/lib/api';

export default function DocumentsPage() {
  const [file,setFile]=useState<File|null>(null); const [language,setLanguage]=useState('eng'); const [text,setText]=useState(''); const [error,setError]=useState(''); const [busy,setBusy]=useState(false);
  const run=async()=>{if(!file)return;setBusy(true);setError('');try{const r=await ocrDocument(file,language);setText(r.text);}catch(e){setError(e instanceof Error?e.message:'OCR failed');}finally{setBusy(false);}};
  return <AppShell><PageHeader title="Document Assistant" description="Run page-aware OCR on PDFs and common image formats." />
    <SectionCard title="OCR workspace" description="OCR output is stored as a document job when a persistent database is configured."><div className="space-y-4">
      <input type="file" accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.bmp" onChange={e=>setFile(e.target.files?.[0]||null)} className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
      <input value={language} onChange={e=>setLanguage(e.target.value)} placeholder="Tesseract language, e.g. eng" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm" />
      <button disabled={!file||busy} onClick={run} className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50">{busy?'Running OCR…':'Run OCR'}</button>
      {error && <p className="text-sm text-destructive">{error}</p>}<textarea value={text} onChange={e=>setText(e.target.value)} rows={22} placeholder="OCR output will appear here…" className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm font-mono" />
    </div></SectionCard></AppShell>;
}
