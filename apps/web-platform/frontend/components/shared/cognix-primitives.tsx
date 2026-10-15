import { cn } from '@/lib/utils';
import type { LucideIcon } from 'lucide-react';
import { ArrowRight } from 'lucide-react';
import Link from 'next/link';

export function PageHeader({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          {title}
        </h1>
        {description && (
          <p className="mt-1 text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {action && <div className="flex items-center gap-2">{action}</div>}
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  tone?: 'primary' | 'success' | 'warning' | 'danger' | 'neutral';
  href?: string;
  trend?: string;
}

export function MetricCard({
  label,
  value,
  icon: Icon,
  tone = 'primary',
  href,
  trend,
}: MetricCardProps) {
  const toneClasses = {
    primary: 'text-primary bg-primary/10 border-primary/20',
    success: 'text-success bg-success/10 border-success/20',
    warning: 'text-warning bg-warning/10 border-warning/20',
    danger: 'text-destructive bg-destructive/10 border-destructive/20',
    neutral: 'text-muted-foreground bg-muted border-border',
  };

  const glowClasses = {
    primary: 'hover:glow-cyan',
    success: 'hover:glow-success',
    warning: 'hover:glow-warning',
    danger: 'hover:glow-danger',
    neutral: '',
  };

  const content = (
    <div
      className={cn(
        'group surface-elevated rounded-xl p-5 transition-all duration-300 hover:border-border/80 hover:-translate-y-0.5',
        glowClasses[tone],
        href && 'cursor-pointer'
      )}
    >
      <div className="flex items-start justify-between">
        <div
          className={cn(
            'flex h-10 w-10 items-center justify-center rounded-lg border transition-transform group-hover:scale-105',
            toneClasses[tone]
          )}
        >
          <Icon className="h-5 w-5" />
        </div>
        {trend && (
          <span className="text-[11px] font-medium text-muted-foreground">
            {trend}
          </span>
        )}
      </div>
      <div className="mt-4">
        <p className="text-3xl font-semibold font-mono-tight text-foreground">
          {value}
        </p>
        <p className="mt-1 text-sm text-muted-foreground">{label}</p>
      </div>
      {href && (
        <div className="mt-3 flex items-center gap-1 text-[11px] font-medium text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100">
          View details <ArrowRight className="h-3 w-3" />
        </div>
      )}
    </div>
  );

  if (href) {
    return <Link href={href}>{content}</Link>;
  }
  return content;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border/50 bg-background-surface/50 px-6 py-16 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted/30 border border-border/40">
        <Icon className="h-6 w-6 text-muted-foreground/60" />
      </div>
      <h3 className="mt-4 text-base font-medium text-foreground">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm text-muted-foreground">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export function SectionCard({
  title,
  description,
  action,
  children,
  className,
}: {
  title?: string;
  description?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn('surface-elevated rounded-xl', className)}>
      {(title || action) && (
        <div className="flex items-center justify-between border-b border-border/40 px-5 py-4">
          <div>
            {title && (
              <h2 className="text-sm font-semibold text-foreground">{title}</h2>
            )}
            {description && (
              <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>
            )}
          </div>
          {action}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
}

export function GlowButton({
  children,
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className={cn(
        'btn-glow inline-flex items-center justify-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-all hover:bg-primary/90 active:scale-[0.98]',
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function FilterChip({
  label,
  active,
  onClick,
  count,
}: {
  label: string;
  active?: boolean;
  onClick?: () => void;
  count?: number;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-all',
        active
          ? 'border-primary/30 bg-primary/10 text-primary'
          : 'border-border/50 bg-background-elevated text-muted-foreground hover:text-foreground hover:border-border'
      )}
    >
      {label}
      {count !== undefined && (
        <span
          className={cn(
            'rounded-full px-1.5 text-[10px]',
            active ? 'bg-primary/20 text-primary' : 'bg-muted text-muted-foreground'
          )}
        >
          {count}
        </span>
      )}
    </button>
  );
}
