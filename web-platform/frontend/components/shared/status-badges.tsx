import { cn } from '@/lib/utils';
import {
  Circle,
  Clock,
  Loader2,
  CheckCircle2,
  GitBranch,
  AlertTriangle,
  Archive,
  FileText,
  FileCheck,
  PlayCircle,
  Radio,
} from 'lucide-react';
import type { SourceStatus, TrustLevel, Priority } from '@/lib/mockData';

const statusConfig: Record<
  SourceStatus,
  { label: string; className: string; icon: typeof Circle; dot: string }
> = {
  new: {
    label: 'New',
    className: 'bg-primary/10 text-primary border-primary/20',
    icon: Circle,
    dot: 'bg-primary',
  },
  processing: {
    label: 'Processing',
    className: 'bg-accent/10 text-accent border-accent/20',
    icon: Loader2,
    dot: 'bg-accent',
  },
  needs_review: {
    label: 'Needs Review',
    className: 'bg-warning/10 text-warning border-warning/20',
    icon: FileText,
    dot: 'bg-warning',
  },
  approved: {
    label: 'Approved',
    className: 'bg-success/10 text-success border-success/20',
    icon: CheckCircle2,
    dot: 'bg-success',
  },
  delivered: {
    label: 'Delivered',
    className: 'bg-primary/10 text-primary border-primary/20',
    icon: GitBranch,
    dot: 'bg-primary',
  },
  failed: {
    label: 'Failed',
    className: 'bg-destructive/10 text-destructive border-destructive/20',
    icon: AlertTriangle,
    dot: 'bg-destructive',
  },
  outdated: {
    label: 'Outdated',
    className: 'bg-muted text-muted-foreground border-border',
    icon: Archive,
    dot: 'bg-muted-foreground',
  },
};

export function StatusBadge({
  status,
  size = 'sm',
}: {
  status: SourceStatus;
  size?: 'sm' | 'md';
}) {
  const config = statusConfig[status];
  const Icon = config.icon;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border font-medium',
        config.className,
        size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs'
      )}
    >
      <Icon
        className={cn(
          'shrink-0',
          size === 'sm' ? 'h-3 w-3' : 'h-3.5 w-3.5',
          status === 'processing' && 'animate-spin'
        )}
      />
      {config.label}
    </span>
  );
}

export function StatusDot({ status }: { status: SourceStatus }) {
  const config = statusConfig[status];
  return (
    <span className="inline-flex items-center gap-2">
      <span className={cn('status-dot', config.dot)} />
      <span className="text-xs text-muted-foreground">{config.label}</span>
    </span>
  );
}

const trustConfig: Record<TrustLevel, { label: string; className: string }> = {
  verified: { label: 'Verified', className: 'bg-success/10 text-success border-success/20' },
  high: { label: 'High Trust', className: 'bg-primary/10 text-primary border-primary/20' },
  medium: { label: 'Medium Trust', className: 'bg-warning/10 text-warning border-warning/20' },
  low: { label: 'Low Trust', className: 'bg-muted text-muted-foreground border-border' },
  unverified: { label: 'Unverified', className: 'bg-destructive/10 text-destructive border-destructive/20' },
};

export function TrustBadge({ trust }: { trust: TrustLevel }) {
  const config = trustConfig[trust];
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2 py-0.5 text-[11px] font-medium',
        config.className
      )}
    >
      {config.label}
    </span>
  );
}

const priorityConfig: Record<Priority, { label: string; className: string; icon: typeof Radio }> = {
  critical: { label: 'Critical', className: 'text-destructive', icon: Radio },
  high: { label: 'High', className: 'text-warning', icon: Radio },
  normal: { label: 'Normal', className: 'text-muted-foreground', icon: Circle },
  low: { label: 'Low', className: 'text-muted-foreground/60', icon: Circle },
};

export function PriorityFlag({ priority }: { priority: Priority }) {
  const config = priorityConfig[priority];
  const Icon = config.icon;
  return (
    <span className={cn('inline-flex items-center gap-1 text-[11px] font-medium', config.className)}>
      <Icon className={cn('h-3 w-3', priority === 'critical' && 'animate-pulse-soft')} />
      {config.label}
    </span>
  );
}

const deliveryStatusConfig: Record<
  string,
  { label: string; className: string; icon: typeof Circle }
> = {
  queued: { label: 'Queued', className: 'bg-muted text-muted-foreground border-border', icon: Clock },
  sending: { label: 'Sending', className: 'bg-accent/10 text-accent border-accent/20', icon: Loader2 },
  delivered: { label: 'Delivered', className: 'bg-primary/10 text-primary border-primary/20', icon: CheckCircle2 },
  acknowledged: { label: 'Acknowledged', className: 'bg-success/10 text-success border-success/20', icon: FileCheck },
  retry_pending: { label: 'Retry Pending', className: 'bg-warning/10 text-warning border-warning/20', icon: AlertTriangle },
  failed: { label: 'Failed', className: 'bg-destructive/10 text-destructive border-destructive/20', icon: AlertTriangle },
  duplicate_ignored: { label: 'Duplicate Ignored', className: 'bg-muted text-muted-foreground border-border', icon: Archive },
};

export function DeliveryStatusBadge({ status }: { status: string }) {
  const config = deliveryStatusConfig[status] || deliveryStatusConfig.queued;
  const Icon = config.icon;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium',
        config.className
      )}
    >
      <Icon className={cn('h-3 w-3 shrink-0', status === 'sending' && 'animate-spin')} />
      {config.label}
    </span>
  );
}

const serviceStatusConfig: Record<
  string,
  { label: string; dot: string; className: string }
> = {
  operational: { label: 'Operational', dot: 'bg-success', className: 'text-success' },
  degraded: { label: 'Degraded', dot: 'bg-warning', className: 'text-warning' },
  down: { label: 'Down', dot: 'bg-destructive', className: 'text-destructive' },
};

export function ServiceStatusBadge({ status }: { status: string }) {
  const config = serviceStatusConfig[status] || serviceStatusConfig.operational;
  return (
    <span className="inline-flex items-center gap-2">
      <span className={cn('status-dot animate-pulse-soft', config.dot)} />
      <span className={cn('text-xs font-medium', config.className)}>{config.label}</span>
    </span>
  );
}

export function PlayIcon() {
  return <PlayCircle className="h-3.5 w-3.5" />;
}
