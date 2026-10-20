'use client';

import React, { useState } from 'react';
import {
  Trophy,
  Flame,
  Zap,
  CheckCircle2,
  ChevronRight,
  Sparkles,
  Award,
  BookOpen,
  Brain,
  Star
} from 'lucide-react';

export function CognixQuestWidget() {
  const [xp, setXp] = useState(7450);
  const [level, setLevel] = useState(8);
  const [streak, setStreak] = useState(14);
  const [claimed, setClaimed] = useState(false);

  const nextLevelXp = 10000;
  const progressPercent = Math.min(100, Math.round((xp / nextLevelXp) * 100));

  const handleClaimWorkflow = () => {
    if (claimed) return;
    setXp(prev => prev + 500);
    setClaimed(true);
  };

  return (
    <div className="rounded-2xl border border-violet-500/20 bg-gradient-to-b from-[#131126]/90 to-[#0b0d19]/90 p-5 backdrop-blur-xl shadow-2xl select-none">
      {/* Top Header: Level & Streak */}
      <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
        <div className="flex items-center gap-3">
          <div className="relative flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-cyan-500 p-0.5 shadow-lg shadow-violet-500/20">
            <div className="flex h-full w-full items-center justify-center rounded-[10px] bg-[#0b0d19]">
              <Trophy className="h-5 w-5 text-amber-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold uppercase tracking-wider text-violet-400">
                LEVEL {level}
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-300 border border-violet-500/20 font-semibold">
                Cyber Scholar
              </span>
            </div>
            <h3 className="text-sm font-semibold text-white">Daily Intelligence Quest</h3>
          </div>
        </div>

        {/* Streak Counter */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-400">
          <Flame className="h-4 w-4 fill-orange-400 animate-bounce" />
          <span className="text-xs font-mono font-bold">{streak} DAYS</span>
        </div>
      </div>

      {/* XP Progress Bar */}
      <div className="my-4">
        <div className="flex items-center justify-between text-xs font-mono mb-1.5">
          <span className="text-slate-400 flex items-center gap-1">
            <Zap className="h-3.5 w-3.5 text-cyan-400" /> XP Progress
          </span>
          <span className="text-cyan-300 font-semibold">
            {xp.toLocaleString()} / {nextLevelXp.toLocaleString()} XP ({progressPercent}%)
          </span>
        </div>
        <div className="h-2.5 w-full rounded-full bg-white/[0.06] overflow-hidden p-0.5 border border-white/[0.05]">
          <div
            className="h-full rounded-full bg-gradient-to-r from-violet-500 via-cyan-400 to-emerald-400 transition-all duration-700 ease-out shadow-lg shadow-cyan-500/30"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Daily Quests List */}
      <div className="space-y-2.5">
        {/* Quest 1 */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <div className="flex items-center gap-3">
            <span className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="h-4 w-4" />
            </span>
            <div>
              <p className="text-xs font-medium text-white line-through opacity-70">
                Synthesize 1 ArXiv Paper
              </p>
              <p className="text-[10px] text-emerald-400 font-mono">+250 XP earned</p>
            </div>
          </div>
          <span className="text-[10px] font-mono font-bold text-emerald-400">DONE</span>
        </div>

        {/* Quest 2 */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-white/[0.03] border border-white/[0.06]">
          <div className="flex items-center gap-3">
            <span className="p-1.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <Brain className="h-4 w-4" />
            </span>
            <div>
              <p className="text-xs font-medium text-white">Review 3 Flashcards</p>
              <p className="text-[10px] text-slate-400 font-mono">Progress: 2 / 3 reviewed</p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20">
            +150 XP
          </span>
        </div>

        {/* Quest 3 */}
        <div className="flex items-center justify-between p-3 rounded-xl bg-violet-500/[0.06] border border-violet-500/20">
          <div className="flex items-center gap-3">
            <span className="p-1.5 rounded-lg bg-violet-500/10 text-violet-400 border border-violet-500/20">
              <Sparkles className="h-4 w-4" />
            </span>
            <div>
              <p className="text-xs font-medium text-white">Execute 1 Workflow Pipeline</p>
              <p className="text-[10px] text-violet-300 font-mono">Automate knowledge ingest</p>
            </div>
          </div>
          <button
            onClick={handleClaimWorkflow}
            disabled={claimed}
            className={`px-3 py-1 text-xs font-semibold rounded-lg transition-all ${
              claimed
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                : 'bg-gradient-to-r from-violet-500 to-cyan-500 hover:opacity-90 text-slate-950 font-bold shadow-md'
            }`}
          >
            {claimed ? 'CLAIMED' : 'CLAIM +500 XP'}
          </button>
        </div>
      </div>

      {/* Badges Footer */}
      <div className="mt-4 pt-3 border-t border-white/[0.06] flex items-center justify-between text-[11px] text-slate-400">
        <span className="flex items-center gap-1.5">
          <Award className="h-3.5 w-3.5 text-amber-400" /> 3 Badges Unlocked
        </span>
        <span className="text-violet-400 font-medium hover:underline cursor-pointer flex items-center gap-0.5">
          View Trophy Vault <ChevronRight className="h-3 w-3" />
        </span>
      </div>
    </div>
  );
}

export default CognixQuestWidget;
