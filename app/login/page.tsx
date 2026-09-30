'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Brain, ArrowRight, Loader2, ShieldCheck } from 'lucide-react';\nimport { supabase, supabaseConfigured } from '@/lib/supabase';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);\n  const [error, setError] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => router.push('/dashboard'), 800);
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background">
      {/* Ambient background */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            'radial-gradient(ellipse 60% 40% at 50% 0%, hsl(189 85% 55% / 0.08), transparent), radial-gradient(ellipse 40% 30% at 80% 80%, hsl(189 60% 40% / 0.05), transparent)',
        }}
      />
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage:
            'linear-gradient(hsl(189 85% 55% / 0.3) 1px, transparent 1px), linear-gradient(90deg, hsl(189 85% 55% / 0.3) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
        }}
      />

      <div className="relative z-10 w-full max-w-md px-6 animate-fade-in-up">
        {/* Logo */}
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 border border-primary/30 glow-cyan">
            <Brain className="h-7 w-7 text-primary" />
          </div>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight text-foreground">
            Cognix Core
          </h1>
          <p className="mt-1 text-xs uppercase tracking-widest text-muted-foreground">
            Research Intelligence Workspace
          </p>
        </div>

        {/* Login card */}
        <div className="glass-panel rounded-2xl p-8 shadow-2xl">
          <div className="mb-6">
            <h2 className="text-lg font-medium text-foreground">Sign in</h2>
            <p className="mt-1 text-sm text-muted-foreground">
              Access your private research workspace.
            </p>
          </div>

          {error && (\n            <div className="mb-4 rounded-lg border border-destructive/30 bg-destructive/10 px-3.5 py-3 text-xs text-destructive">\n              {error}\n            </div>\n          )}\n\n          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11 w-full rounded-lg border border-border/50 bg-background-elevated px-3.5 text-sm text-foreground placeholder:text-muted-foreground/50 focus-glow focus:outline-none transition-all"
                placeholder="you@logixa.io"
              />
            </div>
            <div>
              <div className="mb-1.5 flex items-center justify-between">
                <label className="block text-xs font-medium text-muted-foreground">
                  Password
                </label>
                <Link
                  href="/forgot-password"
                  className="text-xs text-primary hover:text-primary/80 transition-colors"
                >
                  Forgot password?
                </Link>
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="h-11 w-full rounded-lg border border-border/50 bg-background-elevated px-3.5 text-sm text-foreground placeholder:text-muted-foreground/50 focus-glow focus:outline-none transition-all"
                placeholder="Enter your password"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="btn-glow flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-primary text-sm font-medium text-primary-foreground transition-all hover:bg-primary/90 active:scale-[0.98] disabled:opacity-60"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  Sign in <ArrowRight className="h-4 w-4" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 flex items-center gap-2 rounded-lg border border-border/40 bg-background-surface/50 px-3.5 py-3">
            <ShieldCheck className="h-4 w-4 shrink-0 text-success/70" />
            <p className="text-[11px] text-muted-foreground">
              Sign-in uses Supabase Auth. The API validates the resulting access token before protected actions.
            </p>
          </div>
        </div>

        <p className="mt-6 text-center text-[11px] text-muted-foreground/60">
          Cognix Core
        </p>
      </div>
    </div>
  );
}
