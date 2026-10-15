'use client';

import { useEffect, useState, type ComponentType } from 'react';
import { Cpu, HardDrive, Languages, ListChecks, ShieldCheck, Sparkles, Send, Activity, RefreshCw } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { getUsage, type ApiUsage } from '@/lib/api';

export default function UsagePage() {
  const [usage, setUsage] = useState<ApiUsage>({
    ai_requests_today: 0,
    processing_jobs: 0,
    translation_requests: 0,
    drive_exports: 0,
  });
  const [loading, setLoading] = useState(true);

  const fetchUsage = () => {
    setLoading(true);
    getUsage()
      .then(setUsage)
      .catch(() => undefined)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchUsage();
  }, []);

  const aiSummary = usage.ai_summary;
  const providers = aiSummary?.providers ? Object.entries(aiSummary.providers) : [];
  const activeProvidersCount = providers.filter(([_, p]) => p.status === 'active').length;
  const total429Errors = providers.reduce((sum, [_, p]) => sum + (p.errors_today || 0), 0);

  return (
    <AppShell>
      <PageHeader
        title="Usage & AI Resilience Hub"
        description="Live metering across research pipeline, multi-provider AI failover, and Telegram alerts."
        action={
          <button
            type="button"
            onClick={fetchUsage}
            className="flex items-center gap-2 rounded-lg border border-border/60 bg-background-elevated px-3 py-1.5 text-xs font-medium text-foreground hover:bg-muted/40 transition"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        }
      />

      {/* Primary KPI Grid */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Metric label="AI Requests Today" value={usage.ai_requests_today} limit={1000} icon={Cpu} />
        <Metric label="Processing Jobs" value={usage.processing_jobs} limit={100} icon={ListChecks} />
        <Metric label="Translation Requests" value={usage.translation_requests} limit={500} icon={Languages} />
        <Metric label="Drive Exports" value={usage.drive_exports} limit={100} icon={HardDrive} />
      </div>

      {/* AI Failover Architecture */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <SectionCard title="Multi-Model Failover Chains" description="Automatic failover paths on HTTP 429 quota exhaustion">
          <div className="space-y-4">
            <div className="rounded-lg border border-border/40 bg-muted/20 p-3.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-primary">Chat & Knowledge Extraction</span>
                <span className="text-[10px] font-mono text-muted-foreground">5-Stage Failover</span>
              </div>
              <p className="mt-2 text-xs text-foreground font-mono leading-relaxed">
                <span className="text-primary font-bold">1. Gemini 2.5/3.5</span> &rarr; 2. Groq (Qwen-27B) &rarr; 3. Cohere &rarr; 4. Cloudflare &rarr; 5. OpenRouter
              </p>
            </div>

            <div className="rounded-lg border border-border/40 bg-muted/20 p-3.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-cyan-400">RAG Vector Embeddings (1536-D)</span>
                <span className="text-[10px] font-mono text-muted-foreground">Compatible High-D</span>
              </div>
              <p className="mt-2 text-xs text-foreground font-mono leading-relaxed">
                <span className="text-cyan-400 font-bold">1. Voyage AI (voyage-4)</span> &rarr; 2. Cohere (embed-v4.0) &rarr; 3. Cloudflare BGE-Large
              </p>
            </div>
          </div>
        </SectionCard>

        <SectionCard title="Quota Monitoring & Telegram Alerts" description="Native proactive alerting on provider exhaustion">
          <div className="space-y-3.5">
            <div className="flex items-center justify-between rounded-lg border border-emerald-500/20 bg-emerald-500/10 p-3">
              <div className="flex items-center gap-2.5">
                <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs font-semibold text-emerald-300">Telegram Direct Alert</span>
              </div>
              <span className="rounded-md bg-emerald-500/20 px-2 py-0.5 text-[10px] font-bold text-emerald-300">
                Live (Topic #Cognix-Nexus)
              </span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg border border-border/40 bg-muted/20 p-3">
                <p className="text-[11px] text-muted-foreground">Operational Providers</p>
                <p className="mt-1 font-mono text-xl font-bold text-foreground">
                  {providers.length > 0 ? `${activeProvidersCount} / ${providers.length}` : 'All Ready'}
                </p>
              </div>
              <div className="rounded-lg border border-border/40 bg-muted/20 p-3">
                <p className="text-[11px] text-muted-foreground">429 Failovers Dispatched</p>
                <p className={`mt-1 font-mono text-xl font-bold ${total429Errors > 0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                  {total429Errors}
                </p>
              </div>
            </div>
          </div>
        </SectionCard>
      </div>

      {/* Provider Details Table */}
      {providers.length > 0 && (
        <div className="mt-6">
          <SectionCard title="AI Provider Health & Metrics" description="Individual key status and today's query distribution">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-border/40 text-muted-foreground">
                    <th className="pb-3 font-semibold">Provider</th>
                    <th className="pb-3 font-semibold">Status</th>
                    <th className="pb-3 text-right font-semibold">Calls Today</th>
                    <th className="pb-3 text-right font-semibold">Total Calls</th>
                    <th className="pb-3 text-right font-semibold">429 Errors</th>
                    <th className="pb-3 font-semibold">Resilience Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/20">
                  {providers.map(([name, stat]) => {
                    const isExhausted = stat.status.includes('exhausted');
                    const isActive = stat.status === 'active';
                    return (
                      <tr key={name} className="hover:bg-muted/10 transition">
                        <td className="py-3 font-semibold capitalize text-foreground">{name}</td>
                        <td className="py-3">
                          <span
                            className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                              isActive
                                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                : isExhausted
                                ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                                : 'bg-muted text-muted-foreground border border-border/40'
                            }`}
                          >
                            {stat.status}
                          </span>
                        </td>
                        <td className="py-3 text-right font-mono text-foreground">{stat.calls_today}</td>
                        <td className="py-3 text-right font-mono text-muted-foreground">{stat.total_calls}</td>
                        <td className={`py-3 text-right font-mono font-semibold ${stat.errors_today > 0 ? 'text-rose-400' : 'text-muted-foreground'}`}>
                          {stat.errors_today}
                        </td>
                        <td className="py-3 text-muted-foreground">
                          {isExhausted ? 'Telegram alert & switched to next' : 'Ready'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </SectionCard>
        </div>
      )}

      {/* Storage & Pipeline Notes */}
      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <SectionCard title="Knowledge Storage">
          <p className="text-3xl font-semibold font-mono-tight text-foreground">PostgreSQL & PGVector</p>
          <p className="mt-2 text-xs text-muted-foreground">
            1536-dimension pgvector indexes across Voyage-4 embeddings with 40-step sequential SQL migration guard.
          </p>
        </SectionCard>
        <SectionCard title="Metering Notes">
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>• Translation requests reflect processing tasks at the Myanmar localization stage.</li>
            <li>• Drive exports count export jobs, including idempotent retryable jobs.</li>
            <li>• Failed jobs retain audit history for editorial tracking.</li>
          </ul>
        </SectionCard>
      </div>
    </AppShell>
  );
}

function Metric({
  label,
  value,
  limit,
  icon: Icon,
}: {
  label: string;
  value: number;
  limit: number;
  icon: ComponentType<{ className?: string }>;
}) {
  const pct = Math.min(100, (value / limit) * 100);
  return (
    <div className="surface-elevated rounded-xl p-5">
      <Icon className="h-5 w-5 text-primary" />
      <p className="mt-4 font-mono-tight text-2xl font-semibold">{value.toLocaleString()}</p>
      <p className="text-xs text-muted-foreground">
        {label} / {limit.toLocaleString()}
      </p>
      <div className="mt-3 h-1.5 rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
