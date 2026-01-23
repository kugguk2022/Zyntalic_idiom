
import React from 'react';
import { TranslationEngine, TranslationConfig } from '../types';

interface SettingsBarProps {
  config: TranslationConfig;
  onChange: (updates: Partial<TranslationConfig>) => void;
}

const SOURCE_LANGUAGES = [
  'English', 'Spanish', 'French', 'German', 'Chinese',
  'Japanese', 'Korean', 'Russian', 'Portuguese', 'Italian',
  'Arabic', 'Hindi', 'Dutch', 'Turkish'
];

const TARGET_LANGUAGES = [
  'Zyntalic',
  ...SOURCE_LANGUAGES,
];

const SettingsBar: React.FC<SettingsBarProps> = ({ config, onChange }) => {
  return (
    <div className="bg-slate-900/50 border border-slate-800 p-6 rounded-2xl space-y-8 backdrop-blur-sm">
      <div className="space-y-4">
        <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Engine Architecture</label>
        <select 
          value={config.engine}
          onChange={(e) => onChange({ engine: e.target.value as TranslationEngine })}
          className="w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-lg px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all appearance-none cursor-pointer"
        >
          {Object.values(TranslationEngine).map((engine) => (
            <option key={engine} value={engine}>{engine}</option>
          ))}
        </select>
      </div>

      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <label className="text-xs font-bold text-slate-400 uppercase tracking-widest">Mirror Threshold</label>
          <span className="mono text-indigo-400 font-bold">{config.mirror.toFixed(2)}</span>
        </div>
        <input 
          type="range"
          min="0"
          max="1"
          step="0.01"
          value={config.mirror}
          onChange={(e) => onChange({ mirror: parseFloat(e.target.value) })}
          className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
        />
        <div className="flex justify-between text-[10px] text-slate-500 uppercase tracking-tighter">
          <span>Literal</span>
          <span>Adaptive</span>
        </div>
      </div>

      <div className="space-y-4">
        <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Linguistic Vectors</label>
        <div className="space-y-3">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 uppercase ml-1">Source</span>
            <select 
              value={config.sourceLang}
              onChange={(e) => onChange({ sourceLang: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 appearance-none cursor-pointer"
            >
              <option value="Auto-detect">Auto-detect Language</option>
              {SOURCE_LANGUAGES.map(lang => (
                <option key={`src-${lang}`} value={lang}>{lang}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 uppercase ml-1">Target</span>
            <select 
              value={config.targetLang}
              onChange={(e) => onChange({ targetLang: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 appearance-none cursor-pointer"
            >
              {TARGET_LANGUAGES.map(lang => (
                <option key={`tgt-${lang}`} value={lang}>{lang}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsBar;
