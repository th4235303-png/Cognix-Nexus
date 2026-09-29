'use client';

import { useState } from 'react';
import Link from 'next/link';
import { Brain, ArrowLeft, ArrowRight, Loader2, MailCheck } from 'lucide-react';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSent(true);
    }, 800);
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background">
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          backgroundImage:
            'radial-gradient(ellipse 60% 40% at 50% 0%, hsl(189 85% 55% / 0.08), transparent)',
        }}
      />
      <div className="relative z-10 w-full max-w-md px-6 animate-fade-in-up">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 border border-primary/30 glow-cyan">
            <Brain className="h-7 w-7 text-primary" />
          </div>
          <h1 className="mt-4 text-2xl font-semibold tracking-tight text-foreground">
            Reset Password
          </h1>
        </div>

        <div className="glass-panel rounded-2xl p-8 shadow-2xl">
          {sent ? (
            <div className="text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-success/10 border border-success/20">
                <MailCheck className="h-6 w-6 text-success" />
              </div>
              <h2 className="mt-4 text-lg font-medium text-foreground">Check your email</h2>
              <p className="mt-2 text-sm text-muted-foreground">
                If an account exists for <span className="text-foreground font-medium">{email || 'that address'}</span>, you'll receive a reset link shortly.
              </p>
              <Link
                href="/login"
                className="mt-6 inline-flex items-center gap-2 text-sm text-primary hover:text-primary/80 transition-colors"
              >
                <ArrowLeft className="h-4 w-4" /> Back to sign in
              </Link>
            </div>
          ) : (
            <>
              <p className="mb-6 text-sm text-muted-foreground">
                Enter your email address and we'll send you a link to reset your password.
              </p>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="h-11 w-full rounded-lg border border-border/50 bg-background-elevated px-3.5 text-sm text-foreground placeholder:text-muted-foreground/50 focus-glow focus:outline-none transition-all"
                    placeholder="you@logixa.io"
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
                      Send reset link <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </form>
              <Link
                href="/login"
                className="mt-6 flex items-center justify-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              >
                <ArrowLeft className="h-4 w-4" /> Back to sign in
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
