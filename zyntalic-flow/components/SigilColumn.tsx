import React from 'react';

interface SigilColumnProps {
  sigil: string | null;
  type: string | null;
}

const toneByType: Record<string, string> = {
  Reflection: 'text-emerald-300',
  Irony: 'text-amber-300',
  neutral: 'text-slate-500',
};

const SigilColumn: React.FC<SigilColumnProps> = ({ sigil, type }) => {
  const label = type ?? 'neutral';
  const tone = toneByType[label] ?? toneByType.neutral;

  return (
    <div className="w-10 shrink-0 flex flex-col items-center gap-1 pt-1">
      <div className={`text-2xl leading-none ${tone}`}>
        {sigil ?? '·'}
      </div>
      <div className="text-[10px] uppercase tracking-[0.18em] text-slate-500 text-center">
        {label}
      </div>
    </div>
  );
};

export default SigilColumn;
