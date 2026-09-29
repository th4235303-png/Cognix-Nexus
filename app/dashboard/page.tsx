'use client';

import Link from 'next/link';
import {
  Sparkles,
  Loader2,
  FileText,
  CheckCircle2,
  AlertTriangle,
  GitBranch,
  Plus,
  ListChecks,
  ArrowRight,
  Activity,
  Cpu,
  HardDrive,
} from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import {
  PageHeader,
  MetricCard,
  SectionCard,
  GlowButton,
} from '@/components/shared/cognix-primitives';
import { StatusBadge, PriorityFlag, ServiceStatusBadge } from '@/components/shared/status-badges';
import {
  dashboardMetrics,
  processingTasks,
  reviewQueue,
  activityLog,
  usageData,
  serviceHealth,
} from '@/lib/mockData';
import { cn } from '@/lib/utils';

const stages = [
  { label: 'Queued', key: 'queued' },
  { label: 'Extracting', key: 'extracting' },
  { label: 'Cleaning', key: 'cleaning' },
  { label: 'Translating', key: 'translating' },
  { label: 'Summarizing', key: 'summarizing' },
  { label: 'Key Points', key: 'key_points' },
  { label: 'Fact-check', key: 'fact_check' },
  { label: 'Trust Score', key: 'trust_scoring' },
  { label: 'Needs Review', key: 'needs_review' },
  { label: 'Approved', key: 'approved' },
];

export default function DashboardPage() {
  const activeTasks = processingTasks.filter((t) => t.status === 'running');
  const failedTasks = processingTasks.filter((t) => t.status === 'failed');
  const storageWarning = usageData.storageUsed >= 70;

  return (
    <AppShell>
      <PageHeader
        title="Command Center"
        description="Real-time overview of your research intelligence pipeline."
        action={
          <Link href="/sources/add">
            <GlowButton>
              <Plus className="h-4 w-4" /> Add Source
            </GlowButton>
          </Link>
        }
      />

      {/* Metric cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-3 xl:grid-cols-6">
        <MetricCard
          label="New"
          value={dashboardMetrics.new}
          icon={Sparkles}
          tone="primary"
          href="/sources/inbox"
        />
        <MetricCard
          label="Processing"
          value={dashboardMetrics.processing}
          icon={Loader2}
          tone="primary"
          href="/processing"
        />
        <MetricCard
          label="Needs Review"
          value={dashboardMetrics.needsReview}
          icon={FileText}
          tone="warning"
          href="/review"
        />
        <MetricCard
          label="Approved"
          value={dashboardMetrics.approved}
          icon={CheckCircle2}
          tone="success"
          href="/approved"
        />
        <MetricCard
          label="Failed"
          value={dashboardMetrics.failed}
          icon={AlertTriangle}
          tone="danger"
          href="/processing"
        />
        <MetricCard
          label="Delivered"
          value={dashboardMetrics.delivered}
          icon={GitBranch}
          tone="primary"
          href="/delivery"
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        {/* Processing pipeline */}
        <div className="lg:col-span-2">
          <SectionCard
            title="Processing Pipeline"
            description="Live status of extraction, Myanmar translation, review, and approval tasks"
            action={
              <Link
                href="/processing"
                className="text-xs text-primary hover:text-primary/80 transition-colors"
              >
                View all
              </Link>
            }
          >
            {/* Stepper */}
            <div className="mb-6 flex items-center gap-1 overflow-x-auto scrollbar-cognix pb-2">
              {stages.map((stage, i) => (
                <div key={stage.key} className="flex items-center gap-1 shrink-0">
                  <div
                    className={cn(
                      'flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-medium transition-all',
                      i <= 3
                        ? 'border-primary/30 bg-primary/10 text-primary'
                        : 'border-border/40 bg-muted/30 text-muted-foreground'
                    )}
                  >
                    <span
                      className={cn(
                        'h-1.5 w-1.5 rounded-full',
                        i <= 3 ? 'bg-primary animate-pulse-soft' : 'bg-muted-foreground/40'
                      )}
                    />
                    {stage.label}
                  </div>
                  {i < stages.length - 1 && (
                    <div
                      className={cn(
                        'h-px w-4',
                        i < 3 ? 'bg-primary/30' : 'bg-border/40'
                      )}
                    />
                  )}
                </div>
              ))}
            </div>

            {/* Active tasks */}
            <div className="space-y-3">
              {activeTasks.map((task) => (
                <div
                  key={task.id}
                  className="rounded-lg border border-border/40 bg-background-surface/50 p-4 transition-colors hover:border-border/60"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-foreground">
                        {task.sourceTitle}
                      </p>
                      <p className="mt-0.5 font-mono-tight text-[11px] text-muted-foreground">
                        {task.id} · {task.stage} · {task.duration}
                      </p>
                    </div>
                    <span className="font-mono-tight text-sm font-medium text-primary">
                      {task.progress}%
                    </span>
                  </div>
                  <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary transition-all duration-500"
                      style={{ width: `${task.progress}%` }}
                    >
                      <div className="h-full w-full animate-pulse-soft bg-primary/80" />
                    </div>
                  </div>
                </div>
              ))}
              {failedTasks.map((task) => (
                <div
                  key={task.id}
                  className="rounded-lg border border-destructive/20 bg-destructive/5 p-4"
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate text-sm font-medium text-foreground">
                        {task.sourceTitle}
                      </p>
                      <p className="mt-0.5 font-mono-tight text-[11px] text-destructive/80">
                        {task.id} · Failed · {task.retryCount} retries
                      </p>
                    </div>
                    <Link
                      href="/processing"
                      className="shrink-0 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-1 text-[11px] font-medium text-destructive hover:bg-destructive/20 transition-colors"
                    >
                      Retry
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          {/* Review priority queue */}
          <SectionCard title="Review Priority Queue" description="Sources awaiting editorial review">
            <div className="space-y-2">
              {reviewQueue.slice(0, 4).map((source) => (
                <Link
                  key={source.id}
                  href={`/sources/${source.id}`}
                  className="flex items-center gap-3 rounded-lg border border-border/30 bg-background-surface/40 p-3 transition-all hover:border-border/60 hover:bg-white/[0.02]"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium text-foreground">
                      {source.title}
                    </p>
                    <p className="mt-0.5 text-[11px] text-muted-foreground">
                      {source.publisher} · {source.freshness}
                    </p>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-1">
                    <StatusBadge status={source.status} />
                    <PriorityFlag priority={source.priority} />
                  </div>
                </Link>
              ))}
            </div>
            <Link
              href="/review"
              className="mt-4 flex items-center justify-center gap-1.5 rounded-md border border-border/40 py-2 text-xs font-medium text-primary hover:bg-primary/5 transition-colors"
            >
              Open Review Center <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </SectionCard>

          {/* Service health */}
          <SectionCard title="Service Health">
            <div className="space-y-2.5">
              {serviceHealth.map((service) => (
                <div
                  key={service.name}
                  className="flex items-center justify-between"
                >
                  <span className="text-sm text-foreground">{service.name}</span>
                  <div className="flex items-center gap-3">
                    <span className="font-mono-tight text-[11px] text-muted-foreground">
                      {service.latency}
                    </span>
                    <ServiceStatusBadge status={service.status} />
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>

      {/* Bottom row */}
      <div className="mt-6 grid gap-6 lg:grid-cols-3">
        {/* Recent activity */}
        <div className="lg:col-span-2">
          <SectionCard
            title="Recent Activity"
            action={
              <Link
                href="/activity"
                className="text-xs text-primary hover:text-primary/80 transition-colors"
              >
                View all
              </Link>
            }
          >
            <div className="space-y-1">
              {activityLog.slice(0, 6).map((entry) => (
                <div
                  key={entry.id}
                  className="flex items-center gap-3 rounded-md px-2 py-2 transition-colors hover:bg-white/[0.02]"
                >
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted border border-border/40 text-[10px] font-medium text-muted-foreground">
                    {entry.avatar}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-foreground">
                      <span className="font-medium">{entry.user}</span>{' '}
                      <span className="text-muted-foreground">{entry.action}</span>{' '}
                      <span className="font-mono-tight text-primary">{entry.target}</span>
                    </p>
                    <p className="text-[11px] text-muted-foreground">
                      <span className="font-mono-tight">{entry.timestamp}</span>
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>

        {/* Usage snapshot */}
        <div className="space-y-6">
          <SectionCard title="Usage Snapshot">
            <div className="space-y-4">
              {/* AI Requests */}
              <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Cpu className="h-3.5 w-3.5" /> AI Requests Today
                  </span>
                  <span className="font-mono-tight text-xs text-foreground">
                    {usageData.aiRequestsToday.toLocaleString()} / {usageData.aiRequestsLimit.toLocaleString()}
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary transition-all duration-700"
                    style={{
                      width: `${(usageData.aiRequestsToday / usageData.aiRequestsLimit) * 100}%`,
                    }}
                  />
                </div>
              </div>

              {/* Storage */}
                <div>
                <div className="mb-1.5 flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <HardDrive className="h-3.5 w-3.5" /> Storage
                  </span>
                  <span
                    className={cn(
                      'font-mono-tight text-xs',
                      storageWarning ? 'text-warning' : 'text-foreground'
                    )}
                  >
                    {usageData.storageUsed}%
                  </span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-muted">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all duration-700',
                      storageWarning ? 'bg-warning glow-warning' : 'bg-success'
                    )}
                    style={{ width: `${usageData.storageUsed}%` }}
                  />
                </div>
                {storageWarning && (
                  <p className="mt-1.5 text-[11px] text-warning/80">
                    Approaching warning threshold. Consider archiving old sources.
                  </p>
                )}
              </div>

              {/* Delivery events */}
              <div className="flex items-center justify-between border-t border-border/30 pt-3">
                <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Activity className="h-3.5 w-3.5" /> Delivery Events
                </span>
                <div className="flex items-center gap-2">
                  <span className="font-mono-tight text-sm font-medium text-foreground">
                    {usageData.deliveryEvents}
                  </span>
                  <span className="text-[11px] text-success">{usageData.deliveryTrend}</span>
                </div>
              </div>
            </div>
          </SectionCard>

          {/* Quick actions */}
          <div className="grid grid-cols-1 gap-2">
            <Link
              href="/sources/add"
              className="flex items-center gap-3 rounded-lg border border-border/40 bg-background-elevated px-4 py-3 transition-all hover:border-primary/30 hover:bg-primary/5"
            >
              <Plus className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-foreground">Add Source</span>
            </Link>
            <Link
              href="/review"
              className="flex items-center gap-3 rounded-lg border border-border/40 bg-background-elevated px-4 py-3 transition-all hover:border-primary/30 hover:bg-primary/5"
            >
              <ListChecks className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-foreground">Open Review Center</span>
            </Link>
            <Link
              href="/delivery"
              className="flex items-center gap-3 rounded-lg border border-border/40 bg-background-elevated px-4 py-3 transition-all hover:border-primary/30 hover:bg-primary/5"
            >
              <GitBranch className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-foreground">Open Delivery Center</span>
            </Link>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
