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

const EVIDENTIALITIES = [
  { value: 'direct', label: 'Direct Witness' },
  { value: 'inferential', label: 'Inferential' },
  { value: 'hearsay', label: 'Hearsay' },
  { value: 'assumptive', label: 'Assumptive' },
];

const REGISTERS = [
  { value: 'formal', label: 'Formal' },
  { value: 'informal', label: 'Informal' },
  { value: 'literary', label: 'Literary' },
  { value: 'archaic', label: 'Archaic' },
  { value: 'technical', label: 'Technical' },
];

const DIALECTS = [
  { value: 'standard', label: 'Standard' },
  { value: 'northern', label: 'Northern' },
  { value: 'southern', label: 'Southern' },
  { value: 'coastal', label: 'Coastal' },
  { value: 'mountain', label: 'Mountain' },
];

const ANCHORS = [
  'Homer_Iliad',
  'Homer_Odyssey',
  'Plato_Republic',
  'Aristotle_Organon',
  'Virgil_Aeneid',
  'Dante_DivineComedy',
  'Shakespeare_Sonnets',
  'Goethe_Faust',
  'Cervantes_DonQuixote',
  'Milton_ParadiseLost',
  'Melville_MobyDick',
  'Darwin_OriginOfSpecies',
  'Austen_PridePrejudice',
  'Tolstoy_WarPeace',
  'Dostoevsky_BrothersKaramazov',
  'Laozi_TaoTeChing',
  'Sunzi_ArtOfWar',
  'Descartes_Meditations',
  'Bacon_NovumOrganum',
  'Spinoza_Ethics',
];

const selectClassName = 'w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 appearance-none cursor-pointer';

const formatAnchor = (anchor: string): string =>
  anchor.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2');

const SettingsBar: React.FC<SettingsBarProps> = ({ config, onChange }) => {
  const targetLabel = config.engine.includes('Reverse') ? 'English' : 'Zyntalic';

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
              className={selectClassName}
            >
              <option value="Auto-detect">Auto-detect Language</option>
              {SOURCE_LANGUAGES.map((lang) => (
                <option key={`src-${lang}`} value={lang}>{lang}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 uppercase ml-1">Target</span>
            <div className="w-full bg-slate-950 border border-slate-700 text-slate-200 rounded-lg px-3 py-2 text-sm">
              {targetLabel}
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Scope Memory</label>
        <div className="grid grid-cols-1 gap-3">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 uppercase ml-1">Register</span>
            <select
              value={config.register}
              onChange={(e) => onChange({ register: e.target.value })}
              className={selectClassName}
            >
              {REGISTERS.map((register) => (
                <option key={register.value} value={register.value}>{register.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 uppercase ml-1">Dialect</span>
            <select
              value={config.dialect}
              onChange={(e) => onChange({ dialect: e.target.value })}
              className={selectClassName}
            >
              {DIALECTS.map((dialect) => (
                <option key={dialect.value} value={dialect.value}>{dialect.label}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 uppercase ml-1">Evidentiality</span>
            <select
              value={config.evidentiality}
              onChange={(e) => onChange({ evidentiality: e.target.value })}
              className={selectClassName}
            >
              {EVIDENTIALITIES.map((evidentiality) => (
                <option key={evidentiality.value} value={evidentiality.value}>{evidentiality.label}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Frame Pair</label>
        <div className="space-y-3">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 uppercase ml-1">Frame A</span>
            <select
              value={config.frameA}
              onChange={(e) => onChange({ frameA: e.target.value })}
              className={selectClassName}
            >
              <option value="">No Anchor Bias</option>
              {ANCHORS.map((anchor) => (
                <option key={`frame-a-${anchor}`} value={anchor}>{formatAnchor(anchor)}</option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 uppercase ml-1">Frame B</span>
            <select
              value={config.frameB}
              onChange={(e) => onChange({ frameB: e.target.value })}
              className={selectClassName}
            >
              <option value="">No Counter-Frame</option>
              {ANCHORS.map((anchor) => (
                <option key={`frame-b-${anchor}`} value={anchor}>{formatAnchor(anchor)}</option>
              ))}
            </select>
          </div>
        </div>
        <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500">
          Pair anchors to hold the passage between two literary poles.
        </p>
      </div>
    </div>
  );
};

export default SettingsBar;
