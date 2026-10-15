'use client';
import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import {
  Activity, AlertTriangle, CheckCircle2, FileText, GitBranch,
  Loader2, Plus, Sparkles,
} from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import {
  PageHeader, MetricCard, SectionCard, GlowButton, EmptyState,
} from '@/components/shared/cognix-primitives';
import { StageBadge } from '@/components/research/workspace-ui';
import {
  apiSourceToSource, getActivity, getReady,
  listExports, listProcessing, listSources,
  type ApiProcessingTask, type ApiSource,
} from '@/lib/api';

// ─── Brain Soul types ──────────────────────────────────────────────
interface BrainSoulStatus {
  total_syntheses?: number;
  soul_file_entries?: number;
  latest_synthesis_period?: string;
  latest_synthesis_at?: string;
  approved_memories?: number;
  latest_synthesis_snippet?: string;
}

interface YtChannel {
  id: number;
  channel_id: string;
  channel_name: string | null;
  channel_url: string;
  is_active: boolean;
  last_polled_at: string | null;
}

// ─── Pastel colors ──────────────────────────────────────────────────
const P = {
  blue: '#7eb8d4',
  green: '#7ec4a0',
  lav: '#b4a4cc',
  amber: '#c9a96a',
  border: 'rgba(255,255,255,0.07)',
  dim: 'rgba(255,255,255,0.28)',
  bg: 'rgba(22,25,34,0.85)',
};

function fmtD(iso: string | null | undefined) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// ─── Brain Soul Section ─────────────────────────────────────────────
function BrainSoulSection() {
  const [data, setData] = useState<BrainSoulStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [synthesizing, setSynthesizing] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    fetch('/v1/brain/soul/status', { credentials: 'include' })
      .then((r) => r.json())
      .then((d) => { setData(d as BrainSoulStatus); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  async function synthesize() {
    setSynthesizing(true);
    setMsg(null);
    try {
      const r = await fetch('/v1/brain/soul/synthesize', { method: 'POST', credentials: 'include' });
      setMsg(r.ok ? 'Synthesis started.' : 'Synthesis failed.');
    } catch { setMsg('Request error.'); }
    finally { setSynthesizing(false); }
  }

  return (
    <SectionCard
      title="Brain Soul"
      description="Weekly synthesis · context memory · intelligence layer"
    >
      <style>{`@keyframes breathe{0%,100%{opacity:.4}50%{opacity:1}}`}</style>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 6, marginBottom: 12 }}>
        <span style={{ display: 'inline-block', width: 7, height: 7, borderRadius: '50%', background: P.lav, marginTop: 4, animation: 'breathe 4s ease-in-out infinite' }} />
        <span style={{ fontSize: 11, color: P.lav, letterSpacing: '.6px', textTransform: 'uppercase' }}>Soul Layer Active</span>
      </div>

      {loading ? (
        <div style={{ fontSize: 12, color: P.dim }}>Loading brain status…</div>
      ) : data ? (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10, marginBottom: 14 }}>
            {[
              { label: 'Soul Entries', value: data.soul_file_entries ?? 0, color: P.blue },
              { label: 'Syntheses', value: data.total_syntheses ?? 0, color: P.green },
              { label: 'Memories', value: data.approved_memories ?? 0, color: P.lav },
              { label: 'Period', value: data.latest_synthesis_period ?? '—', color: P.amber },
            ].map(({ label, value, color }) => (
              <div
                key={label}
                style={{ background: 'rgba(255,255,255,0.03)', border: `1px solid ${P.border}`, borderRadius: 8, padding: '9px 12px' }}
              >
                <div style={{ fontSize: 10, color: P.dim, marginBottom: 2 }}>{label}</div>
                <div style={{ fontSize: 17, fontWeight: 700, color }}>{value}</div>
              </div>
            ))}
          </div>

          <div style={{ fontSize: 11, color: P.dim, marginBottom: 10 }}>
            <span style={{ color: P.lav, marginRight: 4 }}>Last synthesis:</span>{fmtD(data.latest_synthesis_at)}
          </div>

          {data.latest_synthesis_snippet && (
            <div style={{ fontSize: 11, color: '#94a3b8', borderLeft: `2px solid ${P.lav}`, paddingLeft: 10, lineHeight: 1.65, marginBottom: 14 }}>
              {data.latest_synthesis_snippet.slice(0, 200)}{(data.latest_synthesis_snippet.length ?? 0) > 200 ? '…' : ''}
            </div>
          )}

          {msg && <div style={{ fontSize: 11, color: P.green, marginBottom: 10 }}>{msg}</div>}

          <button
            onClick={synthesize}
            disabled={synthesizing}
            style={{
              fontSize: 11, color: P.green, background: 'transparent',
              border: `1px solid ${P.green}`, borderRadius: 6,
              padding: '4px 12px', cursor: synthesizing ? 'not-allowed' : 'pointer',
              opacity: synthesizing ? 0.5 : 1,
            }}
          >
            {synthesizing ? 'Running…' : 'Synthesize Now'}
          </button>
        </>
      ) : (
        <div style={{ fontSize: 12, color: P.dim }}>Brain status unavailable.</div>
      )}
    </SectionCard>
  );
}

// ─── YouTube Tracker Section ────────────────────────────────────────
function YoutubeTrackerSection() {
  const [channels, setChannels] = useState<YtChannel[]>([]);
  const [url, setUrl] = useState('');
  const [polling, setPolling] = useState(false);
  const [adding, setAdding] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      const r = await fetch('/v1/brain/youtube/channels', { credentials: 'include' });
      if (r.ok) setChannels(await r.json() as YtChannel[]);
    } catch { /* ignore */ }
  }

  useEffect(() => { void load(); }, []);

  async function addChannel() {
    if (!url.trim()) return;
    setAdding(true); setMsg(null); setError(null);
    try {
      const r = await fetch('/v1/brain/youtube/channels', {
        method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel_url: url }),
      });
      if (r.ok) { setMsg('Channel added.'); setUrl(''); void load(); }
      else { const d = await r.json(); setError(d.detail ?? 'Failed to add channel'); }
    } catch { setError('Request failed'); }
    finally { setAdding(false); }
  }

  async function poll() {
    setPolling(true); setMsg(null);
    try {
      const r = await fetch('/v1/brain/youtube/poll', { method: 'POST', credentials: 'include' });
      setMsg(r.ok ? 'Poll started in background.' : 'Poll request failed.');
    } catch { setMsg('Poll request failed.'); }
    finally { setPolling(false); }
  }

  return (
    <SectionCard
      title="YouTube Auto-Tracker"
      description="RSS-based channel tracking · no API key required"
      action={
        <button
          onClick={poll}
          disabled={polling}
          style={{
            fontSize: 11, color: P.blue, background: 'transparent',
            border: `1px solid ${P.blue}`, borderRadius: 6,
            padding: '4px 10px', cursor: polling ? 'not-allowed' : 'pointer',
            opacity: polling ? 0.5 : 1,
          }}
        >
          {polling ? 'Polling…' : 'Poll Now'}
        </button>
      }
    >
      <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="YouTube channel URL or ID"
          style={{
            flex: 1, padding: '7px 10px', borderRadius: 7,
            border: `1px solid ${P.border}`, background: 'rgba(255,255,255,0.04)',
            color: '#f8fafc', fontSize: 12,
          }}
        />
        <button
          onClick={addChannel}
          disabled={adding || !url.trim()}
          style={{
            fontSize: 12, color: P.green, background: 'transparent',
            border: `1px solid ${P.green}`, borderRadius: 6,
            padding: '5px 12px', cursor: 'pointer', whiteSpace: 'nowrap',
          }}
        >
          {adding ? '…' : 'Add'}
        </button>
      </div>

      {msg && <div style={{ fontSize: 11, color: P.green, marginBottom: 8 }}>{msg}</div>}
      {error && <div style={{ fontSize: 11, color: '#f87171', marginBottom: 8 }}>{error}</div>}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {channels.length === 0 ? (
          <div style={{ fontSize: 12, color: P.dim, textAlign: 'center', padding: '16px 0' }}>
            No channels tracked yet.
          </div>
        ) : channels.map((ch) => (
          <div
            key={ch.id}
            style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              padding: '8px 12px',
              background: 'rgba(255,255,255,0.02)',
              border: `1px solid ${P.border}`,
              borderRadius: 8, fontSize: 12,
            }}
          >
            <div>
              <div style={{ color: '#f8fafc', fontWeight: 500 }}>
                {ch.channel_name ?? ch.channel_id}
              </div>
              <div style={{ fontSize: 10, color: P.dim, marginTop: 2 }}>
                Last polled: {fmtD(ch.last_polled_at)}
              </div>
            </div>
            <span style={{
              width: 7, height: 7, borderRadius: '50%',
              background: ch.is_active ? P.green : P.dim,
              display: 'inline-block', animation: ch.is_active ? 'breathe 4s ease-in-out infinite' : 'none',
            }} />
          </div>
        ))}
      </div>

      <div style={{ marginTop: 10 }}>
        <Link
          href="/knowledge"
          style={{ fontSize: 11, color: P.blue, textDecoration: 'none' }}
        >
          View knowledge base →
        </Link>
      </div>
    </SectionCard>
  );
}

// ─── Stage constants ────────────────────────────────────────────────
const stages = [
  'queued', 'extracting', 'cleaning', 'translating', 'summarizing',
  'key_points', 'fact_check', 'trust_scoring', 'needs_review', 'approved',
] as const;

// ─── Main Dashboard ─────────────────────────────────────────────────
export default function DashboardPage() {
  const [sources, setSources] = useState<ApiSource[]>([]);
  const [tasks, setTasks] = useState<ApiProcessingTask[]>([]);
  const [exports, setExports] = useState<{ id: string; source_id: string; status: string; drive_reference: string | null }[]>([]);
  const [activity, setActivity] = useState<Record<string, unknown>[]>([]);
  const [ready, setReady] = useState<{ status: string; persistence_mode: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      listSources(), listProcessing(), listExports(), getActivity(), getReady(),
    ]).then(([s, t, e, a, r]) => {
      setSources(s.items);
      setTasks(t.items);
      setExports(e.items);
      setActivity(a.items);
      setReady(r);
    }).catch((e) => setError(e instanceof Error ? e.message : 'Unable to load dashboard data.'))
      .finally(() => setLoading(false));
  }, []);

  const counts = useMemo(() => ({
    new: sources.filter((s) => s.status === 'new').length,
    processing: sources.filter((s) => s.status === 'processing').length,
    review: sources.filter((s) => s.status === 'needs_review').length,
    approved: sources.filter((s) => s.status === 'approved').length,
    failed: sources.filter((s) => s.status === 'failed').length,
    delivered: exports.filter((e) => e.status === 'exported').length,
  }), [sources, exports]);

  const active = tasks.filter(
    (t) => t.status !== 'completed' && t.stage !== 'needs_review' && t.stage !== 'approved'
  ).slice(0, 5);

  const review = sources
    .filter((s) => s.status === 'needs_review')
    .slice(0, 5)
    .map(apiSourceToSource);

  return (
    <AppShell>
      <PageHeader
        title="Command Center"
        description="Live overview of the Cognix Core research intelligence pipeline."
        action={
          <Link href="/sources/add">
            <GlowButton><Plus className="h-4 w-4" /> Add Source</GlowButton>
          </Link>
        }
      />

      {error && (
        <div role="alert" className="mb-5 rounded-lg border border-destructive/25 bg-destructive/5 p-3 text-xs text-destructive">
          {error}
        </div>
      )}

      {/* KPI Metrics */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
        <MetricCard label="New" value={counts.new} icon={Sparkles} tone="primary" href="/sources/inbox" />
        <MetricCard label="Processing" value={counts.processing} icon={Loader2} tone="primary" href="/processing" />
        <MetricCard label="Needs Review" value={counts.review} icon={FileText} tone="warning" href="/review" />
        <MetricCard label="Approved" value={counts.approved} icon={CheckCircle2} tone="success" href="/approved" />
        <MetricCard label="Failed" value={counts.failed} icon={AlertTriangle} tone="danger" href="/processing" />
        <MetricCard label="Drive Exported" value={counts.delivered} icon={GitBranch} tone="primary" href="/delivery" />
      </div>

      {loading ? (
        <div className="mt-6 flex items-center gap-2 rounded-lg border border-border/40 p-5 text-sm text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />Loading live system state…
        </div>
      ) : (
        <>
          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            {/* Processing pipeline */}
            <div className="lg:col-span-2">
              <SectionCard title="Processing Pipeline" description="Live processing tasks from the backend.">
                <div className="mb-5 flex gap-1 overflow-x-auto pb-2">
                  {stages.map((s) => (
                    <span key={s} className="shrink-0 rounded-full border border-border/40 bg-muted/30 px-2.5 py-1 text-[10px] capitalize text-muted-foreground">
                      {s.replace('_', ' ')}
                    </span>
                  ))}
                </div>
                {active.length === 0 ? (
                  <EmptyState icon={CheckCircle2} title="No active processing" description="There are no queued or running tasks right now." />
                ) : (
                  <div className="space-y-3">
                    {active.map((t) => (
                      <div key={t.id} className="rounded-lg border border-border/40 p-4">
                        <div className="flex items-center justify-between gap-3">
                          <div>
                            <Link href={`/sources/${t.source_id}`} className="text-sm font-medium hover:text-primary">
                              {t.source_id}
                            </Link>
                            <p className="mt-1 font-mono-tight text-[10px] text-muted-foreground">
                              {t.id} · retry {t.retry_count}
                            </p>
                          </div>
                          <div className="flex items-center gap-3">
                            <StageBadge stage={t.stage as never} />
                            <span className="font-mono-tight text-xs text-primary">{t.progress}%</span>
                          </div>
                        </div>
                        <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-muted">
                          <div className="h-full rounded-full bg-primary" style={{ width: `${t.progress}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>
            </div>

            {/* Right column */}
            <div className="space-y-6">
              <SectionCard title="Review Queue" description="Sources awaiting editorial review.">
                {review.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No sources awaiting review.</p>
                ) : (
                  <div className="space-y-2">
                    {review.map((s) => (
                      <Link key={s.id} href={`/sources/${s.id}`} className="block rounded-lg border border-border/30 p-3 hover:border-primary/30">
                        <p className="truncate text-sm font-medium">{s.title}</p>
                        <p className="mt-1 text-[11px] text-muted-foreground">{s.publisher} · {s.priority} priority</p>
                      </Link>
                    ))}
                  </div>
                )}
              </SectionCard>

              <SectionCard title="System Status">
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">API</span>
                    <span className="text-success">{ready?.status === 'ready' ? 'Ready' : 'Unavailable'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Persistence</span>
                    <span>{ready?.persistence_mode || 'Unknown'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Drive exports</span>
                    <span>{exports.filter((e) => e.status === 'exported').length} completed</span>
                  </div>
                </div>
              </SectionCard>

              <SectionCard title="AI Resilience & Alerts" description="Native multi-model failover">
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">RAG Embedding</span>
                    <span className="font-mono text-cyan-400">Voyage-4 → Cohere</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Chat & Extraction</span>
                    <span className="font-mono text-foreground">Gemini → Groq</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-muted-foreground">Telegram Quota Alert</span>
                    <span className="text-success font-medium flex items-center gap-1.5">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      Live (429 Trigger)
                    </span>
                  </div>
                </div>
              </SectionCard>
            </div>
          </div>

          {/* ─── Brain Soul + YouTube Tracker ────────────────────── */}
          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <BrainSoulSection />
            <YoutubeTrackerSection />
          </div>

          {/* Recent Activity */}
          <div className="mt-6">
            <SectionCard
              title="Recent Activity"
              action={<Link href="/activity" className="text-xs text-primary">View all</Link>}
            >
              {activity.length === 0 ? (
                <p className="text-sm text-muted-foreground">No activity recorded yet.</p>
              ) : (
                <div className="space-y-2">
                  {activity.slice(0, 6).map((e, i) => (
                    <div key={String(e.id ?? i)} className="flex items-center gap-3 rounded-md border-b border-border/20 px-2 py-2 last:border-0">
                      <Activity className="h-4 w-4 text-primary" />
                      <div>
                        <p className="text-xs font-medium">
                          {String(e.action ?? 'Activity')} <span className="font-normal text-muted-foreground">{String(e.target ?? '')}</span>
                        </p>
                        <p className="text-[10px] text-muted-foreground">{String(e.timestamp ?? '')}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </SectionCard>
          </div>
        </>
      )}
    </AppShell>
  );
}
