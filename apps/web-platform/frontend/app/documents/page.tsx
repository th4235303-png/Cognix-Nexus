'use client';

import { useState } from 'react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { ocrDocument } from '@/lib/api';

export default function DocumentsPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [language, setLanguage] = useState('eng');
  const [text, setText] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const run = async () => {
    if (files.length === 0) return;
    setBusy(true);
    setError('');
    let aggregated = '';
    try {
      for (let i = 0; i < files.length; i++) {
        const r = await ocrDocument(files[i], language);
        aggregated += `\n=== [FILE ${i + 1}/${files.length}: ${files[i].name}] ===\n` + (r.text || '') + '\n';
      }
      setText(aggregated.trim());
    } catch (e) {
      setError(e instanceof Error ? e.message : 'OCR failed');
    } finally {
      setBusy(false);
    }
  };

  return (
    <AppShell>
      <PageHeader title="Document Assistant" description="Run page-aware OCR on PDFs and common image formats (single or bulk)." />
      <SectionCard title="OCR workspace" description="OCR output is stored as a document job when a persistent database is configured.">
        <div className="space-y-4">
          <input
            type="file"
            multiple
            accept=".pdf,.png,.jpg,.jpeg,.webp,.tiff,.bmp"
            onChange={(e) => setFiles(Array.from(e.target.files || []))}
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
          {files.length > 1 && (
            <p className="text-xs text-muted-foreground">
              📦 {files.length} documents selected for batch OCR
            </p>
          )}
          <input
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
            placeholder="Tesseract language, e.g. eng"
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
          />
          <button
            disabled={files.length === 0 || busy}
            onClick={run}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground disabled:opacity-50"
          >
            {busy ? 'Running OCR…' : files.length > 1 ? `Run OCR on ${files.length} Files (Bulk)` : 'Run OCR'}
          </button>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={22}
            placeholder="OCR output will appear here…"
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm font-mono"
          />
        </div>
      </SectionCard>
    </AppShell>
  );
}
