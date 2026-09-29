'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { Menu, Search, Bell, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { notifications } from '@/lib/mockData';

const routeNames: Record<string, string> = {
  dashboard: 'Dashboard',
  sources: 'Sources',
  inbox: 'Inbox',
  all: 'All Sources',
  add: 'Add Source',
  processing: 'Processing Queue',
  review: 'Review Center',
  approved: 'Approved Knowledge',
  collections: 'Collections',
  tags: 'Tags & Topics',
  delivery: 'Delivery Center',
  usage: 'Usage & Limits',
  activity: 'Activity Log',
  settings: 'Settings',
};

function buildBreadcrumbs(pathname: string) {
  const segments = pathname.split('/').filter(Boolean);
  const crumbs: { label: string; href: string }[] = [];
  let path = '';
  for (const seg of segments) {
    path += `/${seg}`;
    const label = routeNames[seg] || seg;
    crumbs.push({ label, href: path });
  }
  return crumbs;
}

export function Header({ onMenuClick }: { onMenuClick: () => void }) {
  const pathname = usePathname();
  const crumbs = buildBreadcrumbs(pathname);
  const unread = notifications.filter((n) => !n.read).length;
  const [showNotif, setShowNotif] = useState(false);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border/40 bg-background/80 px-4 backdrop-blur-xl md:px-6">
      <button
        onClick={onMenuClick}
        className="flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-white/[0.04] transition-colors md:hidden"
        aria-label="Open menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Breadcrumbs */}
      <div className="flex items-center gap-1.5 text-sm overflow-hidden">
        {crumbs.length === 0 ? (
          <span className="text-muted-foreground">Cognix Core</span>
        ) : (
          crumbs.map((crumb, i) => (
            <div key={crumb.href} className="flex items-center gap-1.5 min-w-0">
              {i > 0 && (
                <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground/40" />
              )}
              <Link
                href={crumb.href}
                className={cn(
                  'truncate transition-colors hover:text-primary',
                  i === crumbs.length - 1
                    ? 'text-foreground font-medium'
                    : 'text-muted-foreground'
                )}
              >
                {crumb.label}
              </Link>
            </div>
          ))
        )}
      </div>

      <div className="ml-auto flex items-center gap-2">
        {/* Search */}
        <div className="relative hidden sm:block">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground/50" />
          <input
            type="text"
            placeholder="Search sources..."
            className="h-9 w-48 rounded-md border border-border/50 bg-background-elevated pl-9 pr-3 text-sm text-foreground placeholder:text-muted-foreground/50 focus-glow focus:outline-none transition-all md:w-64"
          />
        </div>

        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setShowNotif(!showNotif)}
            className="relative flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground hover:text-foreground hover:bg-white/[0.04] transition-colors"
            aria-label="Notifications"
          >
            <Bell className="h-4.5 w-4.5" />
            {unread > 0 && (
              <span className="absolute right-1.5 top-1.5 flex h-2 w-2 rounded-full bg-primary animate-pulse-soft" />
            )}
          </button>
          {showNotif && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowNotif(false)}
              />
              <div className="absolute right-0 top-12 z-50 w-80 rounded-lg border border-border/60 bg-popover shadow-2xl animate-slide-in-right">
                <div className="border-b border-border/40 px-4 py-3">
                  <p className="text-sm font-medium text-foreground">Notifications</p>
                </div>
                <div className="max-h-80 overflow-y-auto scrollbar-cognix">
                  {notifications.map((n) => (
                    <Link
                      key={n.id}
                      href={n.link}
                      onClick={() => setShowNotif(false)}
                      className="flex gap-3 border-b border-border/30 px-4 py-3 hover:bg-white/[0.03] transition-colors"
                    >
                      <span
                        className={cn(
                          'mt-1.5 h-2 w-2 shrink-0 rounded-full',
                          n.type === 'error' && 'bg-destructive',
                          n.type === 'warning' && 'bg-warning',
                          n.type === 'success' && 'bg-success',
                          n.type === 'info' && 'bg-primary',
                          !n.read && 'animate-pulse-soft'
                        )}
                      />
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-foreground">{n.title}</p>
                        <p className="text-xs text-muted-foreground line-clamp-2">{n.description}</p>
                        <p className="mt-1 text-[10px] text-muted-foreground/60 font-mono-tight">{n.time}</p>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>

        {/* User avatar */}
        <div className="flex items-center gap-2.5 rounded-md border border-border/40 bg-background-elevated px-2.5 py-1.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/15 border border-primary/20 text-xs font-medium text-primary">
            EV
          </div>
          <div className="hidden md:block">
            <p className="text-xs font-medium text-foreground leading-tight">Elena Vasquez</p>
            <p className="text-[10px] text-muted-foreground leading-tight">Lead Researcher</p>
          </div>
        </div>
      </div>
    </header>
  );
}
