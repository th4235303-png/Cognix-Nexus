'use client';

import { useState, type ReactNode } from 'react';
import { Sidebar, MobileNav } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { cn } from '@/lib/utils';

export function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background">
      {/* Ambient background grid */}
      <div
        className="pointer-events-none fixed inset-0 z-0 opacity-[0.15]"
        style={{
          backgroundImage:
            'radial-gradient(ellipse 80% 50% at 50% -20%, hsl(189 85% 55% / 0.08), transparent)',
        }}
      />

      <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
      <MobileNav open={mobileOpen} setOpen={setMobileOpen} />

      <div
        className={cn(
          'relative z-10 transition-all duration-300',
          collapsed ? 'md:pl-16' : 'md:pl-60'
        )}
      >
        <Header onMenuClick={() => setMobileOpen(true)} />
        <main className="px-4 py-6 md:px-8 md:py-8">
          <div key="page-content" className="animate-fade-in-up">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
