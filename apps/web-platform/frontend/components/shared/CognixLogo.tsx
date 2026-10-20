import React from "react";

interface CognixLogoProps {
  className?: string;
  size?: number;
  showText?: boolean;
}

export function CognixLogo({ className = "", size = 36, showText = true }: CognixLogoProps) {
  return (
    <div className={`flex items-center gap-2.5 select-none ${className}`}>
      {/* Neural Nexus & Infinite Synapse Constellation SVG */}
      <svg
        width={size}
        height={size}
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0 transition-transform hover:scale-105 duration-300"
      >
        <defs>
          <linearGradient id="cognix-violet-grad" x1="6" y1="6" x2="42" y2="42" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#C084FC" />
            <stop offset="40%" stopColor="#8B5CF6" />
            <stop offset="100%" stopColor="#22D3EE" />
          </linearGradient>
          <linearGradient id="cognix-synapse-grad" x1="12" y1="24" x2="36" y2="24" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#A855F7" />
            <stop offset="100%" stopColor="#06B6D4" />
          </linearGradient>
          <filter id="cognix-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="2.5" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Outer Dark Cosmic Shield */}
        <rect
          x="3"
          y="3"
          width="42"
          height="42"
          rx="12"
          fill="#080D1A"
          stroke="url(#cognix-violet-grad)"
          strokeWidth="1.75"
        />

        {/* Neural Network Connections (Synapse Lines) */}
        <g stroke="url(#cognix-synapse-grad)" strokeWidth="1.5" opacity="0.6">
          <line x1="14" y1="24" x2="24" y2="14" />
          <line x1="24" y1="14" x2="34" y2="24" />
          <line x1="34" y1="24" x2="24" y2="34" />
          <line x1="24" y1="34" x2="14" y2="24" />
          <line x1="14" y1="24" x2="34" y2="24" strokeDasharray="2,2" />
        </g>

        {/* Infinite Neural Loop / Möbius Curve forming "C" & "N" Nexus */}
        <path
          d="M17 18C14 21 14 27 17 30C20 33 26 31 28 27C30 23 34 21 37 24C40 27 38 32 34 33"
          stroke="url(#cognix-violet-grad)"
          strokeWidth="3.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter="url(#cognix-glow)"
        />

        {/* Central Spark of Insight (Core Intelligence Node) */}
        <circle cx="24" cy="24" r="3.2" fill="#22D3EE" />
        <circle cx="24" cy="24" r="5.5" stroke="#22D3EE" strokeWidth="1" opacity="0.5" className="animate-ping" />

        {/* Satellite Synapse Nodes */}
        <circle cx="14" cy="24" r="2" fill="#C084FC" />
        <circle cx="24" cy="14" r="2" fill="#A855F7" />
        <circle cx="34" cy="24" r="2" fill="#38BDF8" />
        <circle cx="24" cy="34" r="2" fill="#8B5CF6" />
      </svg>

      {showText && (
        <div className="flex flex-col leading-none">
          <span className="text-[15px] font-black tracking-tight text-white flex items-center gap-1.5">
            COGNIX<span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">NEXUS</span>
          </span>
          <span className="text-[9px] font-semibold uppercase tracking-[0.2em] text-violet-400/80 mt-0.5">
            Second Brain Intelligence
          </span>
        </div>
      )}
    </div>
  );
}

export default CognixLogo;
