import React from 'react';
import { AnchorWeight } from '../types';

interface AnchorBarsProps {
  weights: AnchorWeight[];
}

const shortenAnchor = (anchor: string): string => {
  const trimmed = anchor.includes('_')
    ? anchor.split('_').slice(1).join(' ')
    : anchor;
  return trimmed.replace(/([a-z])([A-Z])/g, '$1 $2');
};

const AnchorBars: React.FC<AnchorBarsProps> = ({ weights }) => {
  const rows = [...weights]
    .sort((left, right) => right.weight - left.weight)
    .slice(0, 5);

  if (rows.length === 0) {
    return null;
  }

  return (
    <div className="mt-4 space-y-2">
      <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">
        Anchor Resonance
      </div>
      {rows.map((row) => (
        <div key={row.name} className="flex items-center gap-3 text-xs">
          <div className="w-36 shrink-0 text-slate-300 truncate" title={row.name}>
            {shortenAnchor(row.name)}
          </div>
          <div className="h-2 flex-1 rounded-full bg-slate-800/80 overflow-hidden">
            <div
              className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-emerald-400 to-lime-300"
              style={{ width: `${Math.max(0, Math.min(100, row.weight * 100))}%` }}
            />
          </div>
          <div className="w-12 shrink-0 text-right text-slate-500 tabular-nums">
            {(row.weight * 100).toFixed(1)}%
          </div>
        </div>
      ))}
    </div>
  );
};

export default AnchorBars;
