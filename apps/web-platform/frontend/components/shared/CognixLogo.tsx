'use client';

import React from 'react';

interface CognixLogoProps {
  className?: string;
  size?: number;
  showText?: boolean;
}

export function CognixLogo({
  className = '',
  size = 40,
  showText = true,
}: CognixLogoProps) {
  return (
    <div className={`flex items-center gap-3 select-none ${className}`}>
      {/* Clean Glowing Cyan Brain Tile (Exact Reference Screenshot Style) */}
      <img
        src="/logo.svg"
        alt="Cognix Core Icon"
        width={size}
        height={size}
        className="shrink-0 object-contain rounded-2xl drop-shadow-[0_0_14px_rgba(0,229,255,0.3)] transition-transform duration-200 hover:scale-105"
      />

      {showText && (
        <div className="flex flex-col leading-none">
          <span className="text-[16px] font-bold tracking-tight text-white">
            Cognix Core
          </span>
          <span className="mt-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
            Brain Vault OS
          </span>
        </div>
      )}
    </div>
  );
}

export default CognixLogo;
