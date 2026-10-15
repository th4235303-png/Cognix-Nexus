'use client';

import { useState } from 'react';
import Link from 'next/link';
import { AlertTriangle, CheckCircle2, ExternalLink, FileCheck2, Flag, HardDrive, Loader2, Save, ShieldCheck } from 'lucide-react';
import { cn } from '@/lib/utils';
import { SectionCard, PageHeader } from '@/components/shared/cognix-primitives';
import type { ClaimState, ExportStatus, ResearchRecord } from '@/lib/researchData';
import { stageLabels } from '@/lib/researchData';
import { approveSource, exportToGoogleDrive, requestSourceRevision, updateSourceTranslation, ApiError } from '@/lib/api';

export function StageBadge({ stage }: { stage: keyof typeof stageLabels }) {
  const tone = ['approved','exported'].includes(stage) ? 'success' : ['failed'].includes(stage) ? 'danger' : ['needs_review','fact_check'].includes(stage) ? 'warning' : 'primary';
  return <span className={cn('inline-flex items-center rounded-full border px-2.5 py-1 text-[11px] font-medium',
    tone === 'success' && 'border-success/25 bg-success/10 text-success',
    tone === 'danger' && 'border-destructive/25 bg-destructive/10 text-destructive',
    tone === 'warning' && 'border-warning/25 bg-warning/10 text-warning',
    tone === 'primary' && 'border-primary/25 bg-primary/10 text-primary'
  )}>{stageLabels[stage]}</span>;
}

export function FlagBadge({ state, label }: { state: ClaimState | string; label: string }) {
  const critical = state === 'conflicted' || state === 'unsupported';
  const warning = state === 'needs_verification' || state === 'pending';
  return <span className={cn('inline-flex items-center gap-1 rounded-full border px-2 py-1 text-[10px] font-medium',
    critical ? 'border-destructive/25 bg-destructive/10 text-destructive' :
    warning ? 'border-warning/25 bg-warning/10 text-warning' : 'border-success/25 bg-success/10 text-success'
  )}><Flag className="h-3 w-3" />{label}</span>;
}

export function TranslationPanel({ record }: { record: ResearchRecord }) {
  const [edited, setEdited] = useState(record.humanEditedMyanmar);
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function saveEdit() {
    if (!edited.trim()) return;
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      await updateSourceTranslation(record.source.id, edited.trim());
      setSaved(true);
    } catch {
      setError('Could not save the human-edited translation.');
    } finally {
      setSaving(false);
    }
  }
  return <SectionCard title="Translation Workflow" description="Keep original, machine translation, human editing, and approved content separate.">
    <div className="grid gap-4 lg:grid-cols-2">
      <TextBlock title="Original source text" value={record.originalText} />
      <TextBlock title="Original-language summary" value={record.originalSummary || 'No summary yet.'} />
      <TextBlock title="Myanmar Translation" value={record.myanmarTranslation || 'Translation pending.'} />
      <div className="rounded-lg border border-border/40 bg-background-surface/40 p-4">
        <div className="mb-2 flex items-center justify-between"><p className="text-xs font-medium text-foreground">Human Edited</p><span className="text-[10px] text-muted-foreground">Backend-persisted edit</span></div>
        <textarea value={edited} onChange={(e) => { setEdited(e.target.value); setSaved(false); }} className="min-h-36 w-full rounded-md border border-border/50 bg-background-elevated p-3 text-sm leading-6 text-foreground focus-glow focus:outline-none" />
        <div className="mt-3 flex items-center justify-between">
          <span className="text-[11px] text-muted-foreground">{error || (saved ? 'Saved to backend.' : 'Edit the translation and save when ready.')}</span>
          <button disabled={saving || !edited.trim()} onClick={saveEdit} className="inline-flex items-center gap-1.5 rounded-md border border-border/50 px-3 py-2 text-xs font-medium hover:border-primary/30 hover:text-primary disabled:cursor-not-allowed disabled:opacity-50"><Save className="h-3.5 w-3.5" /> {saving ? 'Saving…' : 'Save edit'}</button>
        </div>
      </div>
    </div>
    <div className="mt-4 rounded-lg border border-success/20 bg-success/5 p-4">
      <div className="flex items-center gap-2 text-xs font-medium text-success"><CheckCircle2 className="h-4 w-4" /> Approved version</div>
      <p className="mt-2 text-sm leading-6 text-foreground">{record.approvedMyanmar || 'Not approved yet.'}</p>
    </div>
  </SectionCard>;
}

function TextBlock({ title, value }: { title: string; value: string }) {
  return <div className="rounded-lg border border-border/40 bg-background-surface/40 p-4"><p className="mb-2 text-xs font-medium text-foreground">{title}</p><p className="text-sm leading-6 text-muted-foreground">{value}</p></div>;
}

export function ClaimsPanel({ record }: { record: ResearchRecord }) {
  return <SectionCard title="Claims & Evidence" description="Flags indicate review state; they do not independently verify a claim.">
    <div className="space-y-3">
      {record.source.claims.length === 0 && <div className="rounded-lg border border-border/40 p-5 text-sm text-muted-foreground">No extracted claims yet.</div>}
      {record.source.claims.map((claim) => {
        const flag = record.claimFlags.find((f) => f.id === claim.id);
        return <div key={claim.id} className="rounded-lg border border-border/40 bg-background-surface/30 p-4">
          <div className="flex flex-col gap-2 md:flex-row md:items-start md:justify-between">
            <div className="min-w-0"><p className="text-sm font-medium text-foreground">{claim.text}</p><p className="mt-1 text-xs text-muted-foreground">Evidence: {claim.excerpt}</p><p className="mt-2 font-mono-tight text-[10px] text-muted-foreground">{claim.location} · {claim.id}</p></div>
            {flag && <FlagBadge state={claim.verification === 'pending' ? 'needs_verification' : claim.verification} label={flag.label} />}
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground"><span>Confidence {claim.confidence}%</span><span>•</span><span>Source trust: {record.sourceTrust}</span></div>
        </div>;
      })}
    </div>
  </SectionCard>;
}

export function ReviewGate({ record }: { record: ResearchRecord }) {
  const critical = record.claimFlags.filter((f) => f.severity === 'critical');
  const [state, setState] = useState<'needs_review' | 'approved' | 'revision'>('needs_review');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  async function approve() { setBusy(true); setMessage(null); try { await approveSource(record.source.id); setState('approved'); setMessage('Approved by backend.'); } catch (e) { setMessage(e instanceof ApiError && e.status === 409 ? 'Approval blocked by critical warnings.' : 'Approval failed.'); } finally { setBusy(false); } }
  async function revise() { setBusy(true); setMessage(null); try { await requestSourceRevision(record.source.id, 'Human review requested revision.'); setState('revision'); setMessage('Revision requested.'); } catch { setMessage('Revision request failed.'); } finally { setBusy(false); } }
  return <SectionCard title="Approval Gate" description="Critical warnings must be resolved before a record can be approved.">
    {critical.length > 0 && <div className="mb-4 rounded-lg border border-destructive/25 bg-destructive/5 p-4"><div className="flex items-center gap-2 text-sm font-medium text-destructive"><AlertTriangle className="h-4 w-4" /> Critical warnings</div><ul className="mt-2 space-y-1 text-xs text-muted-foreground">{critical.map((f) => <li key={f.id}>• {f.label}: {f.note}</li>)}</ul></div>}
    <div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-sm font-medium text-foreground">Review state</p><p className="text-xs text-muted-foreground">{state === 'approved' ? 'Approved by backend.' : state === 'revision' ? 'Revision requested.' : 'Needs human review before export.'}</p></div>
      <div className="flex gap-2"><button disabled={busy || state === 'approved'} onClick={revise} className="rounded-md border border-border/50 px-3 py-2 text-xs font-medium disabled:opacity-40">{busy ? 'Working…' : 'Request revision'}</button><button disabled={critical.length > 0 || busy || state === 'approved'} onClick={approve} className="inline-flex items-center gap-2 rounded-md bg-success px-4 py-2 text-xs font-medium text-success-foreground disabled:cursor-not-allowed disabled:opacity-40"><ShieldCheck className="h-4 w-4" /> {busy ? 'Approving…' : 'Approve knowledge'}</button></div>
    </div>{message && <p className="mt-3 text-xs text-muted-foreground">{message}</p>}
  </SectionCard>;
}

export function ExportButton({ status, sourceId, disabled = false }: { status: ExportStatus; sourceId: string; disabled?: boolean }) {
  const [state, setState] = useState(status);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  async function exportNow() { setBusy(true); setMessage(null); try { const job = await exportToGoogleDrive(sourceId, `cognix-${sourceId}-${Date.now()}`); setState(job.status as ExportStatus); setMessage('Export queued. Mock Drive mode is active.'); } catch { setMessage('Export failed or source is not approved.'); } finally { setBusy(false); } }
  const canExport = state === 'ready';
  return <div><button disabled={!canExport || disabled || busy} onClick={exportNow} className="inline-flex items-center gap-2 rounded-md border border-primary/30 bg-primary/10 px-3 py-2 text-xs font-medium text-primary disabled:cursor-not-allowed disabled:opacity-40">
    {busy || state === 'queued' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <HardDrive className="h-3.5 w-3.5" />}
    {busy ? 'Queueing…' : state === 'ready' ? 'Export to Google Drive' : state === 'queued' ? 'Queued for export' : state === 'exported' ? 'Exported' : 'Not ready'}
  </button>{message && <p className="mt-2 text-[11px] text-muted-foreground">{message}</p>}</div>;
}

export function ResearchDetail({ record }: { record: ResearchRecord }) {
  const [tab, setTab] = useState<'overview'|'translation'|'claims'|'export'>('overview');
  return <div className="space-y-6">
    <PageHeader title={record.source.title} description={`${record.source.publisher} · ${record.source.author} · ${record.source.topic}`} action={<div className="flex flex-wrap gap-2"><StageBadge stage={record.processingStage} /><Link href="/sources/all" className="inline-flex items-center gap-1.5 rounded-md border border-border/50 px-3 py-2 text-xs hover:border-primary/30 hover:text-primary"><ExternalLink className="h-3.5 w-3.5" /> Back to sources</Link></div>} />
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      <Info label="Source trust" value={record.sourceTrust} />
      <Info label="Claim confidence" value={record.claimConfidence} />
      <Info label="Translation" value={record.translationStatus} />
      <Info label="Export" value={record.exportStatus.replace('_',' ')} />
    </div>
    <div className="flex flex-wrap gap-1 border-b border-border/40 pb-2">
      {(['overview','translation','claims','export'] as const).map((item) => <button key={item} onClick={() => setTab(item)} className={cn('rounded-md px-3 py-2 text-xs font-medium capitalize', tab === item ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:text-foreground')}>{item}</button>)}
    </div>
    {tab === 'overview' && <div className="grid gap-6 lg:grid-cols-2"><SectionCard title="Original / AI Summary"><TextBlock title="Original" value={record.originalText} /><div className="mt-4"><TextBlock title="AI Summary" value={record.originalSummary || 'Pending'} /></div></SectionCard><SectionCard title="Key Points"><ul className="space-y-3">{record.source.keyPoints.map((p) => <li key={p} className="flex gap-2 text-sm text-foreground"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-primary" />{p}</li>)}</ul></SectionCard></div>}
    {tab === 'translation' && <TranslationPanel record={record} />}
    {tab === 'claims' && <ClaimsPanel record={record} />}
    {tab === 'export' && <div className="grid gap-6 lg:grid-cols-2"><SectionCard title="Export status"><div className="flex items-center gap-3"><FileCheck2 className="h-5 w-5 text-primary" /><div><p className="text-sm font-medium">{record.exportStatus}</p><p className="text-xs text-muted-foreground">Approved records only. Prototype uses a mock Drive state.</p></div></div><div className="mt-5"><ExportButton status={record.exportStatus} sourceId={record.source.id} /></div></SectionCard><SectionCard title="Safe reference"><p className="text-xs text-muted-foreground">The UI never exposes OAuth tokens or private credentials.</p><p className="mt-3 rounded-md bg-background-surface p-3 font-mono-tight text-xs text-foreground">{record.driveReference || 'No Drive reference yet.'}</p></SectionCard></div>}
  </div>;
}

function Info({ label, value }: { label: string; value: string }) { return <div className="surface-elevated rounded-lg p-4"><p className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</p><p className="mt-1 text-sm font-medium capitalize text-foreground">{value}</p></div>; }
