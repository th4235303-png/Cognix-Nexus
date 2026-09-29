'use client';

import { useState } from 'react';
import { AlertTriangle, CheckCircle2, Save, Loader2 } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard, GlowButton } from '@/components/shared/cognix-primitives';
import { sources } from '@/lib/mockData';
import { createProcessingTask, createSource } from '@/lib/api';

export default function AddSourcePage() {
  const [url, setUrl] = useState('');
  const [note, setNote] = useState('');
  const [saved, setSaved] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const duplicate = sources.find((s) => url.trim() && s.url.toLowerCase().replace(/\/$/, '') === url.trim().toLowerCase().replace(/\/$/, ''));

  async function queueSource() {
    setError('');
    setSaved(false);
    setBusy(true);
    try {
      const result = await createSource(url.trim(), note.trim());
      await createProcessingTask(result.source.id);
      setSaved(true);
      setUrl('');
      setNote('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to queue source. Check that the Cognix API is running.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <AppShell>
      <PageHeader
        title="Add Source"
        description="Create a research intake record. The source is validated by the FastAPI intake service before processing."
        action={<span className="text-[10px] uppercase tracking-widest text-muted-foreground">API intake</span>}
      />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <SectionCard title="Source intake">
            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium" htmlFor="source-url">URL</label>
                <input
                  id="source-url"
                  type="url"
                  value={url}
                  onChange={(e) => { setUrl(e.target.value); setSaved(false); setError(''); }}
                  placeholder="https://example.com/research"
                  className="h-11 w-full rounded-md border border-border/50 bg-background-elevated px-3 text-sm focus-glow focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium" htmlFor="source-note">Research note</label>
                <textarea
                  id="source-note"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="What should the processor look for?"
                  className="min-h-32 w-full rounded-md border border-border/50 bg-background-elevated p-3 text-sm focus-glow focus:outline-none"
                />
              </div>
              {duplicate && (
                <div className="flex gap-2 rounded-lg border border-warning/25 bg-warning/5 p-4 text-xs text-warning">
                  <AlertTriangle className="h-4 w-4 shrink-0" />
                  <div>
                    <p className="font-medium">Possible duplicate source</p>
                    <p className="mt-1 text-warning/80">{duplicate.title} · {duplicate.id}</p>
                  </div>
                </div>
              )}
              {error && (
                <div role="alert" className="rounded-lg border border-destructive/25 bg-destructive/5 p-4 text-xs text-destructive">
                  {error}
                </div>
              )}
              <GlowButton onClick={queueSource} disabled={busy || !url.trim()}>
                {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                {busy ? 'Queueing…' : 'Queue source'}
              </GlowButton>
              {saved && (
                <p className="flex items-center gap-2 text-xs text-success">
                  <CheckCircle2 className="h-4 w-4" /> Source and processing task queued successfully.
                </p>
              )}
            </div>
          </SectionCard>
        </div>
        <SectionCard title="Ingestion architecture">
          <ul className="space-y-3 text-xs text-muted-foreground">
            <li>1. Validate URL and source metadata.</li>
            <li>2. Detect duplicate URLs safely.</li>
            <li>3. Create a processing task.</li>
            <li>4. Continue through translation → review → approval.</li>
          </ul>
        </SectionCard>
      </div>
    </AppShell>
  );
}
