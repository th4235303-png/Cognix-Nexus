'use client';

import { useState } from 'react';
import { Download, Loader2, CheckCircle2, BookOpen, Brain, Archive, HardDrive } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { exportBrainVault, exportKnowledge } from '@/lib/api';

type ExportStatus = 'idle' | 'loading' | 'done' | 'error';

interface ExportOption {
  id: string;
  title: string;
  description: string;
  format: string;
  icon: React.ComponentType<{ className?: string }>;
  action: () => Promise<void>;
}

export default function ExportPage() {
  const [statuses, setStatuses] = useState<Record<string, ExportStatus>>({});
  const [messages, setMessages] = useState<Record<string, string>>({});

  const setStatus = (id: string, s: ExportStatus, msg?: string) => {
    setStatuses(prev => ({ ...prev, [id]: s }));
    if (msg !== undefined) setMessages(prev => ({ ...prev, [id]: msg }));
  };

  const downloadJson = (data: unknown, filename: string) => {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const downloadMarkdown = (markdown: string, filename: string) => {
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportOptions: ExportOption[] = [
    {
      id: 'vault',
      title: 'Full Brain Vault',
      description:
        'Exports all books, chapters, notes, concepts, links, and generated summaries as a portable JSON package. Secret Vault ciphertext is intentionally excluded.',
      format: 'JSON',
      icon: Archive,
      action: async () => {
        setStatus('vault', 'loading');
        try {
          const data = await exportBrainVault();
          downloadJson(data, 'cognix-brain-vault.json');
          setStatus('vault', 'done', 'Brain Vault exported successfully.');
        } catch {
          setStatus('vault', 'error', 'Export failed. Is the FastAPI backend running?');
        }
      },
    },
    {
      id: 'knowledge-canonical',
      title: 'Canonical Knowledge',
      description:
        'All human-approved canonical knowledge items across all categories, with source lineage preserved. Ideal for downstream use in LLM context.',
      format: 'Markdown',
      icon: Brain,
      action: async () => {
        setStatus('knowledge-canonical', 'loading');
        try {
          const result = await exportKnowledge('canonical');
          downloadMarkdown(result.markdown, 'cognix-knowledge-canonical.md');
          setStatus('knowledge-canonical', 'done', `Exported ${result.total} canonical items.`);
        } catch {
          setStatus('knowledge-canonical', 'error', 'Export failed — ensure knowledge items exist.');
        }
      },
    },
    {
      id: 'knowledge-draft',
      title: 'Draft Knowledge',
      description:
        'AI-distilled knowledge items awaiting human review. Useful for auditing what the model extracted before promotion.',
      format: 'Markdown',
      icon: BookOpen,
      action: async () => {
        setStatus('knowledge-draft', 'loading');
        try {
          const result = await exportKnowledge('draft');
          downloadMarkdown(result.markdown, 'cognix-knowledge-draft.md');
          setStatus('knowledge-draft', 'done', `Exported ${result.total} draft items.`);
        } catch {
          setStatus('knowledge-draft', 'error', 'Export failed — ensure draft knowledge items exist.');
        }
      },
    },
  ];

  return (
    <AppShell>
      <PageHeader
        title="Unified Export"
        description="Export the Brain Vault as a portable, versioned package. Exports run client-side; no data leaves to a third-party."
        action={
          <div className="flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-3 py-1.5 text-[11px] text-primary">
            <HardDrive className="h-3.5 w-3.5" />
            Client-side export
          </div>
        }
      />

      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {exportOptions.map((opt) => {
          const status = statuses[opt.id] ?? 'idle';
          const message = messages[opt.id];
          const Icon = opt.icon;
          return (
            <SectionCard key={opt.id} title={opt.title}>
              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-primary/20 bg-primary/10">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <span className="rounded-full border border-border/50 bg-muted/40 px-2.5 py-0.5 text-[10px] uppercase tracking-widest text-muted-foreground">
                    {opt.format}
                  </span>
                </div>
                <p className="text-sm leading-6 text-muted-foreground">{opt.description}</p>
                {message && (
                  <p
                    role="status"
                    className={`flex items-center gap-1.5 text-xs ${
                      status === 'done' ? 'text-success' : 'text-destructive'
                    }`}
                  >
                    {status === 'done' && <CheckCircle2 className="h-3.5 w-3.5" />}
                    {message}
                  </p>
                )}
                <button
                  disabled={status === 'loading'}
                  onClick={opt.action}
                  aria-label={`Download ${opt.title}`}
                  className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-all hover:bg-primary/90 active:scale-[0.98] disabled:opacity-60"
                >
                  {status === 'loading' ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Exporting…
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4" /> Download {opt.format}
                    </>
                  )}
                </button>
              </div>
            </SectionCard>
          );
        })}
      </div>

      <div className="mt-6">
        <SectionCard title="Export notes">
          <ul className="space-y-2 text-sm text-muted-foreground" aria-label="Export notes">
            <li>• Exports run entirely in the browser. No data is sent to any third-party service.</li>
            <li>• Secret Vault items are stored as encrypted ciphertext only. Plaintext is never included in exports.</li>
            <li>• JSON exports include a full graph of source IDs, book IDs, and chunk lineage to allow re-import.</li>
            <li>• Markdown exports are formatted for use with RAG pipelines, LLM contexts, or Obsidian vaults.</li>
            <li>• For Google Drive delivery, use the <strong>Delivery Center</strong>.</li>
          </ul>
        </SectionCard>
      </div>
    </AppShell>
  );
}
