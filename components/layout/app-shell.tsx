'use client';

import { useEffect, useState, type ReactNode } from 'react';
import { Sidebar, MobileNav } from '@/components/layout/sidebar';
import { Header } from '@/components/layout/header';
import { cn } from '@/lib/utils';
import { supabase, supabaseConfigured } from '@/lib/supabase';
import { useRouter, usePathname } from 'next/navigation';

export function AppShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [authChecking, setAuthChecking] = useState(supabaseConfigured);

  useEffect(() => {
    if (!supabaseConfigured || !supabase) {
      setAuthChecking(false);
      return;
    }
    let active = true;
    supabase.auth.getSession().then(({ data }) => {
      if (!active) return;
      if (!data.session) router.replace('/login');
      setAuthChecking(false);
    });
    const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
      if (!session && pathname !== '/login') router.replace('/login');
    });
    return () => { active = false; listener.subscription.unsubscribe(); };
  }, [pathname, router]);

  if (authChecking) return <div className="min-h-screen bg-background" />;
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
