'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import {
  LayoutDashboard,
  Inbox,
  FileText,
  ListChecks,
  CheckCircle2,
  GitBranch,
  Gauge,
  ScrollText,
  Settings,
  FolderOpen,
  Tags,
  Brain,
  BookOpen,
  Network,
  MessageSquare,
  Sparkles,
  ChevronLeft,
  LogOut,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { supabase } from '@/lib/supabase';

const navSections = [
  {
    label: 'Workspace',
    items: [
      { label: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
      { label: 'Source Inbox', href: '/sources/inbox', icon: Inbox },
      { label: 'All Sources', href: '/sources/all', icon: FileText },
      { label: 'Add Source', href: '/sources/add', icon: ListChecks },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { label: 'Processing Queue', href: '/processing', icon: Gauge },
      { label: 'Review Center', href: '/review', icon: ListChecks },
      { label: 'Approved Knowledge', href: '/approved', icon: CheckCircle2 },
    ],
  },
  {
    label: 'Brain Vault',
    items: [
      { label: 'Book Library', href: '/books', icon: BookOpen },
      { label: 'Second Brain', href: '/notes', icon: Brain },
      { label: 'Brain Query', href: '/chat', icon: MessageSquare },
      { label: 'Level Up 20', href: '/level-up', icon: Sparkles },
      { label: 'Knowledge Graph', href: '/graph', icon: Network },
      { label: 'Language Tutor', href: '/tutor', icon: Brain },
      { label: 'Document OCR', href: '/documents', icon: FileText },
      { label: 'Secret Vault', href: '/vault', icon: FolderOpen },
      { label: 'Unified Export', href: '/export', icon: GitBranch },
      { label: 'Vizora Lens', href: '/lens', icon: Brain },
    ],
  },
  {
    label: 'Organization',
    items: [
      { label: 'Collections', href: '/collections', icon: FolderOpen },
      { label: 'Tags & Topics', href: '/tags', icon: Tags },
    ],
  },
  {
    label: 'Delivery & System',
    items: [
      { label: 'Delivery Center', href: '/delivery', icon: GitBranch },
      { label: 'Usage & Limits', href: '/usage', icon: Gauge },
      { label: 'Activity Log', href: '/activity', icon: ScrollText },
      { label: 'Settings', href: '/settings', icon: Settings },
    ],
  },
];

export function Sidebar({
  collapsed,
  setCollapsed,
}: {
  collapsed: boolean;
  setCollapsed: (v: boolean) => void;
}) {
  const signOut = async () => {
    if (supabase) await supabase.auth.signOut();
    window.location.href = '/login';
  };
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-border/50 bg-background-surface transition-all duration-300',
        collapsed ? 'w-16' : 'w-60'
      )}
    >
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 border-b border-border/40 px-4">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 border border-primary/30 glow-cyan">
          <Brain className="h-5 w-5 text-primary" />
        </div>
        {!collapsed && (
          <div className="animate-fade-in">
            <p className="text-sm font-semibold tracking-tight text-foreground">
              Cognix Core
            </p>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground">
              Logixa Ecosystem
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto scrollbar-cognix py-4">
        {navSections.map((section) => (
          <div key={section.label} className="mb-5">
            {!collapsed && (
              <p className="px-4 mb-1.5 text-[10px] font-medium uppercase tracking-widest text-muted-foreground/70">
                {section.label}
              </p>
            )}
            <div className="space-y-0.5 px-2">
              {section.items.map((item) => {
                const active =
                  pathname === item.href ||
                  (item.href !== '/dashboard' && pathname.startsWith(item.href));
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      'group flex items-center gap-3 rounded-md px-2.5 py-2 text-sm transition-all duration-200',
                      active
                        ? 'bg-primary/10 text-primary border border-primary/20'
                        : 'text-muted-foreground hover:text-foreground hover:bg-white/[0.03] border border-transparent',
                      collapsed && 'justify-center'
                    )}
                    title={collapsed ? item.label : undefined}
                  >
                    <Icon
                      className={cn(
                        'h-4 w-4 shrink-0 transition-colors',
                        active
                          ? 'text-primary'
                          : 'text-muted-foreground group-hover:text-foreground'
                      )}
                    />
                    {!collapsed && <span className="truncate">{item.label}</span>}
                    {!collapsed && item.label === 'Source Inbox' && (
                      <span className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-primary/20 px-1.5 text-[10px] font-medium text-primary">
                        0
                      </span>
                    )}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Collapse toggle + user */}
      <div className="border-t border-border/40 p-3">
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex w-full items-center gap-3 rounded-md px-2.5 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-white/[0.03] transition-colors"
        >
          <ChevronLeft
            className={cn(
              'h-4 w-4 transition-transform',
              collapsed && 'rotate-180'
            )}
          />
          {!collapsed && <span>Collapse</span>}
        </button>
        {!collapsed && (
          <button
            type="button"
            onClick={signOut}
            className="mt-1 flex w-full items-center gap-3 rounded-md px-2.5 py-2 text-sm text-muted-foreground hover:text-destructive hover:bg-destructive/5 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span>Sign out</span>
          </button>
        )}
      </div>
    </aside>
  );
}

export function MobileNav({
  open,
  setOpen,
}: {
  open: boolean;
  setOpen: (v: boolean) => void;
}) {
  const signOut = async () => {
    if (supabase) await supabase.auth.signOut();
    window.location.href = '/login';
  };
  const pathname = usePathname();
  const unreadCount = 0;

  return (
    <>
      {/* Overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden animate-fade-in"
          onClick={() => setOpen(false)}
        />
      )}
      {/* Drawer */}
      <aside
        className={cn(
          'fixed left-0 top-0 z-50 flex h-screen w-64 flex-col border-r border-border/50 bg-background-surface transition-transform duration-300 md:hidden',
          open ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center gap-3 border-b border-border/40 px-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 border border-primary/30">
            <Brain className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="text-sm font-semibold text-foreground">Cognix Core</p>
            <p className="text-[10px] uppercase tracking-widest text-muted-foreground">
              Logixa Ecosystem
            </p>
          </div>
        </div>
        <nav className="flex-1 overflow-y-auto scrollbar-cognix py-4">
          {navSections.map((section) => (
            <div key={section.label} className="mb-5">
              <p className="px-4 mb-1.5 text-[10px] font-medium uppercase tracking-widest text-muted-foreground/70">
                {section.label}
              </p>
              <div className="space-y-0.5 px-2">
                {section.items.map((item) => {
                  const active =
                    pathname === item.href ||
                    (item.href !== '/dashboard' && pathname.startsWith(item.href));
                  const Icon = item.icon;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setOpen(false)}
                      className={cn(
                        'group flex items-center gap-3 rounded-md px-2.5 py-2.5 text-sm transition-all',
                        active
                          ? 'bg-primary/10 text-primary border border-primary/20'
                          : 'text-muted-foreground hover:text-foreground hover:bg-white/[0.03] border border-transparent'
                      )}
                    >
                      <Icon className="h-4 w-4 shrink-0" />
                      <span>{item.label}</span>
                      {item.label === 'Source Inbox' && unreadCount > 0 && (
                        <span className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-primary/20 px-1.5 text-[10px] font-medium text-primary">
                          {unreadCount}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>
        <div className="border-t border-border/40 p-3">
          <button
            type="button"
            onClick={signOut}
            className="flex w-full items-center gap-3 rounded-md px-2.5 py-2.5 text-sm text-muted-foreground hover:text-destructive transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span>Sign out</span>
          </button>
        </div>
      </aside>
    </>
  );
}
