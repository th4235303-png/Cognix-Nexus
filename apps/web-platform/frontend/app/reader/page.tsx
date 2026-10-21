'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, BookOpen, Sparkles, BookMarked, BrainCircuit, Type, FileText } from 'lucide-react';
import { AppShell } from '@/components/layout/app-shell';
import { PageHeader, SectionCard } from '@/components/shared/cognix-primitives';
import { ApiBrainBook, listBrainBooks, getBrainBook, listBookSummaries } from '@/lib/api';

export default function ReaderPage() {
  const [books, setBooks] = useState<ApiBrainBook[]>([]);
  const [selectedBookId, setSelectedBookId] = useState<string>('');
  const [activeBook, setActiveBook] = useState<ApiBrainBook | null>(null);
  const [summaries, setSummaries] = useState<Array<{ id: string; level: string; content: string }>>([]);
  const [fontSize, setFontSize] = useState<'sm' | 'base' | 'lg'>('base');
  const [activeTab, setActiveTab] = useState<'summary' | 'notes' | 'concepts'>('summary');
  const [noteText, setNoteText] = useState('');
  const [savedNotes, setSavedNotes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [streamingText, setStreamingText] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);

  const startStreamSummary = async () => {
    if (!selectedBookId) return;
    setIsStreaming(true);
    setStreamingText('');
    try {
      const response = await fetch(`/api/brain/books/${selectedBookId}/stream-summary`);
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) return;

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.type === 'token') {
                setStreamingText((prev) => prev + data.text);
              } else if (data.type === 'done') {
                setIsStreaming(false);
              }
            } catch {}
          }
        }
      }
    } catch (e) {
      console.error('SSE summary failed', e);
    } finally {
      setIsStreaming(false);
    }
  };


  useEffect(() => {
    listBrainBooks()
      .then((res) => {
        setBooks(res.items);
        if (res.items.length > 0) {
          setSelectedBookId(res.items[0].id);
        }
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedBookId) return;
    getBrainBook(selectedBookId)
      .then(setActiveBook)
      .catch(() => setActiveBook(null));

    listBookSummaries(selectedBookId)
      .then((res) => setSummaries(res.items))
      .catch(() => setSummaries([]));
  }, [selectedBookId]);

  const handleSaveNote = () => {
    if (!noteText.trim()) return;
    setSavedNotes([noteText.trim(), ...savedNotes]);
    setNoteText('');
  };

  const fontClasses = {
    sm: 'text-xs leading-6',
    base: 'text-sm leading-7',
    lg: 'text-base leading-8',
  };

  return (
    <AppShell>
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link href="/books" className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-3.5 w-3.5" /> Book Library
          </Link>
          <span className="text-muted-foreground">/</span>
          <span className="text-xs font-semibold">Split-View Reader</span>
        </div>
        <div className="flex items-center gap-2">
          <Type className="h-4 w-4 text-muted-foreground" />
          <button
            type="button"
            onClick={() => setFontSize('sm')}
            className={`rounded px-2 py-0.5 text-xs font-medium ${fontSize === 'sm' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}
          >
            A-
          </button>
          <button
            type="button"
            onClick={() => setFontSize('base')}
            className={`rounded px-2 py-0.5 text-xs font-medium ${fontSize === 'base' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}
          >
            A
          </button>
          <button
            type="button"
            onClick={() => setFontSize('lg')}
            className={`rounded px-2 py-0.5 text-xs font-medium ${fontSize === 'lg' ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground'}`}
          >
            A+
          </button>
        </div>
      </div>

      <PageHeader
        title="Split-View Knowledge Reader"
        description="Dual-pane focus: Read your primary source on the left while AI synthesizes notes, concepts, and flashcards on the right."
      />

      {/* Book Selector Bar */}
      <div className="mb-4 flex flex-wrap items-center gap-3 rounded-xl border border-border/60 bg-card/60 p-3">
        <BookOpen className="h-4 w-4 text-primary" />
        <span className="text-xs font-medium text-muted-foreground">Active Source:</span>
        <select
          value={selectedBookId}
          onChange={(e) => setSelectedBookId(e.target.value)}
          className="rounded-lg border border-border bg-background px-3 py-1.5 text-xs font-semibold focus:outline-none focus:ring-1 focus:ring-primary"
        >
          {books.map((b) => (
            <option key={b.id} value={b.id}>
              {b.title} ({b.chunk_count} chunks)
            </option>
          ))}
        </select>
        {activeBook && (
          <span className="ml-auto text-xs text-muted-foreground">
            Category: <strong className="text-foreground">{activeBook.category || 'General'}</strong> · Chunks: <strong className="text-foreground">{activeBook.chunk_count}</strong>
          </span>
        )}
      </div>

      {/* Split Dual-Pane View */}
      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        {/* Left Pane: Reading Canvas */}
        <div className="space-y-4">
          <SectionCard
            title={activeBook?.title || 'Document Content'}
            description="Preserved chapters, structured paragraphs, and textual chunks."
          >
            <div className="max-h-[calc(100vh-320px)] space-y-6 overflow-y-auto pr-2">
              {activeBook?.chapters && activeBook.chapters.length > 0 ? (
                activeBook.chapters.map((chapter) => (
                  <section key={chapter.id} className="space-y-3">
                    <h3 className="sticky top-0 bg-background/95 py-1 text-sm font-bold text-primary backdrop-blur">
                      {chapter.chapter_number}. {chapter.title}
                    </h3>
                    <div className="space-y-3">
                      {chapter.chunks?.map((chunk) => (
                        <article
                          key={chunk.id}
                          className="rounded-lg border border-border/40 bg-background/40 p-4 transition-colors hover:border-border"
                        >
                          <p className={`whitespace-pre-wrap text-foreground/90 ${fontClasses[fontSize]}`}>
                            {chunk.content}
                          </p>
                        </article>
                      ))}
                    </div>
                  </section>
                ))
              ) : (
                <div className="py-12 text-center text-sm text-muted-foreground">
                  <FileText className="mx-auto mb-2 h-8 w-8 opacity-40" />
                  <p>No chapter text available or currently reading.</p>
                  <p className="mt-1 text-xs">Upload or import text via the Book Library to start reading.</p>
                </div>
              )}
            </div>
          </SectionCard>
        </div>

        {/* Right Pane: AI Second Brain Companion */}
        <div className="space-y-4">
          <SectionCard
            title="Second Brain Companion"
            description="Real-time knowledge distillation, synthesis, and quick note capture."
          >
            {/* Tabs */}
            <div className="mb-4 flex border-b border-border">
              <button
                type="button"
                onClick={() => setActiveTab('summary')}
                className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-semibold ${activeTab === 'summary' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
              >
                <Sparkles className="h-3.5 w-3.5" /> AI Summary
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('notes')}
                className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-semibold ${activeTab === 'notes' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
              >
                <BookMarked className="h-3.5 w-3.5" /> Quick Notes
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('concepts')}
                className={`flex items-center gap-1.5 border-b-2 px-3 py-2 text-xs font-semibold ${activeTab === 'concepts' ? 'border-primary text-primary' : 'border-transparent text-muted-foreground hover:text-foreground'}`}
              >
                <BrainCircuit className="h-3.5 w-3.5" /> Key Concepts
              </button>
            </div>

            {/* Tab Contents */}
            {activeTab === 'summary' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-border/40">
                  <span className="text-xs font-semibold text-muted-foreground">Neural Synthesis</span>
                  <button
                    type="button"
                    onClick={startStreamSummary}
                    disabled={isStreaming || !selectedBookId}
                    className="inline-flex items-center gap-1.5 rounded-md bg-cyan-500/10 px-2.5 py-1 text-xs font-semibold text-cyan-400 border border-cyan-500/30 hover:bg-cyan-500/20 disabled:opacity-50"
                  >
                    <Sparkles className={`h-3.5 w-3.5 ${isStreaming ? 'animate-spin' : ''}`} />
                    {isStreaming ? 'Streaming Distillation...' : '✨ Stream Live Chapter Synthesis'}
                  </button>
                </div>

                {(streamingText || isStreaming) && (
                  <div className="rounded-lg border border-cyan-500/40 bg-cyan-950/20 p-3 shadow-inner">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="inline-block h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
                      <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400">Live Cognitive Stream</span>
                    </div>
                    <p className="whitespace-pre-wrap text-xs leading-6 text-cyan-100 font-mono">
                      {streamingText}
                      {isStreaming && <span className="inline-block w-1.5 h-3.5 ml-0.5 bg-cyan-400 animate-pulse align-middle" />}
                    </p>
                  </div>
                )}
                {summaries.length > 0 ? (
                  summaries.map((s) => (
                    <div key={s.id} className="rounded-lg border border-border/50 bg-background/50 p-3">
                      <span className="inline-block rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-primary">
                        {s.level}
                      </span>
                      <p className="mt-2 whitespace-pre-wrap text-xs leading-6 text-foreground/90">
                        {s.content}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="rounded-lg border border-dashed border-border p-6 text-center text-xs text-muted-foreground">
                    <Sparkles className="mx-auto mb-2 h-6 w-6 text-primary/60" />
                    AI synthesis is generated in the background as chunks are processed.
                  </div>
                )}
              </div>
            )}

            {activeTab === 'notes' && (
              <div className="space-y-3">
                <div className="space-y-2">
                  <textarea
                    rows={3}
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder="Capture an insight, quote, or note while reading..."
                    className="w-full rounded-lg border border-border bg-background p-2.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                  <button
                    type="button"
                    onClick={handleSaveNote}
                    className="rounded-lg bg-primary px-3 py-1.5 text-xs font-semibold text-primary-foreground hover:bg-primary/90"
                  >
                    Save Note
                  </button>
                </div>
                <div className="mt-4 space-y-2">
                  {savedNotes.map((note, idx) => (
                    <div key={idx} className="rounded-lg border border-border/40 bg-background/30 p-2.5 text-xs leading-5">
                      {note}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'concepts' && (
              <div className="space-y-2 text-xs">
                <p className="text-muted-foreground">Highlighted mental models & vocabulary from this source:</p>
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {['Mental Models', 'Second Order Thinking', 'Spaced Repetition', 'Chunking', 'Active Recall'].map((c, i) => (
                    <span key={i} className="rounded-full border border-border bg-muted/60 px-2.5 py-1 text-[11px] font-medium text-foreground">
                      {c}
                    </span>
                  ))}
                </div>
                <div className="mt-4 rounded-lg border border-primary/20 bg-primary/5 p-3 text-[11px] text-muted-foreground">
                  💡 <strong>Tip:</strong> These concepts are automatically indexed into your <Link href="/level-up" className="text-primary underline">Level Up</Link> flashcard deck.
                </div>
              </div>
            )}
          </SectionCard>
        </div>
      </div>
    </AppShell>
  );
}
