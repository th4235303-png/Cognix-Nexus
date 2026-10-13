'use client';

import { useEffect, useState } from 'react';
import { Settings2, ShieldCheck, Database, Globe, Loader2, CheckCircle2, RefreshCw } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { getReady, getUsage, type ApiUsage } from '@/lib/api';

interface SystemStatus {
  status: string;
  persistence_mode: string;
  database_configured: boolean;
  database_reachable: boolean;
}

const WORKFLOW_SETTINGS: [string, string][] = [
  ['Myanmar translation', 'Enabled — mock provider'],
  ['Human approval gate', 'Required'],
  ['Critical claim warnings', 'Block approval'],
  ['Drive export', 'Backend integration; requires Google OAuth configuration'],
  ['Source deduplication', 'URL-based fingerprint check on intake'],
  ['Processing pipeline', '8-stage: extract → clean → translate → summarize → key-points → fact-check → trust-score → review'],
];

export default function SettingsPage() {
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [usage, setUsage] = useState<ApiUsage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = () => {
    setLoading(true);
    setError(null);
    Promise.all([getReady(), getUsage()])
      .then(([ready, u]) => {
        setSystemStatus(ready);
        setUsage(u);
      })
      .catch(() => setError('Could not fetch system status. Is the FastAPI backend running?'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { refresh(); }, []);

  return (
    <AppShell>
      <PageHeader
        title="Settings"
        description="Environment and workflow preferences. Secrets are intentionally not configurable in the browser."
        action={
          <button
            onClick={refresh}
            aria-label="Refresh system status"
            className="inline-flex items-center gap-2 rounded-md border border-border/50 px-3 py-2 text-xs hover:border-primary/30"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        }
      />

      {error && (
        <div role="alert" className="mb-5 rounded-lg border border-warning/25 bg-warning/5 p-3 text-xs text-warning">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* System health card */}
        <SectionCard
          title="System status"
          description="Live readiness probe from the FastAPI backend."
          action={
            loading
              ? <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
              : systemStatus?.status === 'ready'
              ? <span className="flex items-center gap-1.5 text-xs text-success"><CheckCircle2 className="h-3.5 w-3.5" /> Ready</span>
              : <span className="text-xs text-warning">Unavailable</span>
          }
        >
          <dl className="space-y-3 text-sm">
            {([
              ['API status', systemStatus?.status ?? '—'],
              ['Persistence mode', systemStatus?.persistence_mode ?? '—'],
              ['Database configured', systemStatus?.database_configured ? 'Yes' : 'No'],
              ['Database reachable', systemStatus?.database_reachable ? 'Yes' : 'No'],
            ] as [string, string][]).map(([label, value]) => (
              <div key={label} className="flex items-center justify-between border-b border-border/30 pb-3 last:border-0">
                <dt className="text-muted-foreground">{label}</dt>
                <dd className="font-medium tabular-nums">{value}</dd>
              </div>
            ))}
          </dl>
        </SectionCard>

        {/* Usage snapshot */}
        <SectionCard
          title="Usage snapshot"
          description="Live counters from the backend usage endpoint."
          action={<Globe className="h-4 w-4 text-muted-foreground" />}
        >
          {loading ? (
            <p className="text-sm text-muted-foreground">Loading usage data…</p>
          ) : usage ? (
            <dl className="space-y-3 text-sm">
              {([
                ['AI requests today', usage.ai_requests_today],
                ['Processing jobs', usage.processing_jobs],
                ['Translation requests', usage.translation_requests],
                ['Drive exports', usage.drive_exports],
              ] as [string, number][]).map(([label, value]) => (
                <div key={label} className="flex items-center justify-between border-b border-border/30 pb-3 last:border-0">
                  <dt className="text-muted-foreground">{label}</dt>
                  <dd className="font-mono-tight font-medium">{value.toLocaleString()}</dd>
                </div>
              ))}
            </dl>
          ) : (
            <p className="text-sm text-muted-foreground">Usage data unavailable.</p>
          )}
        </SectionCard>

        {/* Research workflow */}
        <SectionCard
          title="Research workflow"
          description="Immutable pipeline configuration for this deployment."
          action={<Settings2 className="h-4 w-4 text-muted-foreground" />}
        >
          <dl className="space-y-3 text-sm">
            {WORKFLOW_SETTINGS.map(([label, value]) => (
              <div key={label} className="flex items-start justify-between gap-4 border-b border-border/30 pb-3 last:border-0">
                <dt className="shrink-0 text-muted-foreground">{label}</dt>
                <dd className="text-right text-xs text-foreground/80">{value}</dd>
              </div>
            ))}
          </dl>
        </SectionCard>

        {/* Security */}
        <SectionCard
          title="Security"
          description="Credential and authentication boundaries."
          action={<ShieldCheck className="h-4 w-4 text-muted-foreground" />}
        >
          <div className="space-y-4 text-sm text-muted-foreground">
            <p>
              OAuth credentials, refresh tokens, API keys, and provider secrets belong in the backend
              environment or secret manager. No sensitive Drive path or credential is rendered in this client UI.
            </p>
            <p>
              Session tokens are managed by Supabase Auth. The FastAPI backend validates the access token
              on every protected action. Token refresh is handled client-side automatically.
            </p>
            <div className="flex items-center gap-2 rounded-lg border border-success/20 bg-success/5 px-3 py-2.5 text-xs text-success">
              <ShieldCheck className="h-4 w-4 shrink-0" />
              Secrets are encrypted at rest and never exposed to the browser.
            </div>
          </div>
        </SectionCard>

        {/* Environment info */}
        <SectionCard
          title="Environment"
          description="Current deployment configuration."
          action={<Database className="h-4 w-4 text-muted-foreground" />}
          className="lg:col-span-2"
        >
          <dl className="grid gap-3 text-sm sm:grid-cols-2">
            {([
              ['API base URL', process.env.NEXT_PUBLIC_COGNIX_API_URL || 'http://localhost:8000 (default)'],
              ['Supabase configured', process.env.NEXT_PUBLIC_SUPABASE_URL ? 'Yes' : 'No — using open-access mode'],
              ['Frontend environment', process.env.NODE_ENV ?? 'unknown'],
              ['Auth mode', process.env.NEXT_PUBLIC_SUPABASE_URL ? 'Supabase JWT' : 'Open access (dev only)'],
            ] as [string, string][]).map(([label, value]) => (
              <div key={label} className="flex flex-col gap-0.5 border-b border-border/30 pb-3 last:border-0 sm:last:border-0">
                <dt className="text-xs text-muted-foreground">{label}</dt>
                <dd className="font-mono-tight text-xs text-foreground/90 break-all">{value}</dd>
              </div>
            ))}
          </dl>
        </SectionCard>
      </div>
    </AppShell>
  );
}
