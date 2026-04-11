import React from 'react';
import { AnchorMode, TranslationEngine, TranslationConfig } from '../types';

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

const ANCHOR_MODES: Array<{ value: AnchorMode; label: string; description: string }> = [
  { value: 'auto', label: 'Auto Resonance', description: 'Infer anchors from the text.' },
  { value: 'manual', label: 'Manual Set', description: 'Use only the anchors you select.' },
  { value: 'neutral', label: 'Neutral Base', description: 'Disable anchor bias entirely.' },
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

const deriveLegacyFrames = (selectedAnchors: string[]) => ({
  frameA: selectedAnchors[0] || '',
  frameB: selectedAnchors[1] || '',
});

const canonicalizeAnchor = (value: string): string =>
  value.trim().toLowerCase().replace(/[_\s-]+/g, '');

const resolveAnchor = (value: string): string | null => {
  const trimmed = value.trim();
  if (!trimmed) {
    return null;
  }

  const direct = ANCHORS.find((anchor) => anchor === trimmed);
  if (direct) {
    return direct;
  }

  const canonical = canonicalizeAnchor(trimmed);
  return ANCHORS.find((anchor) => {
    return canonicalizeAnchor(anchor) === canonical || canonicalizeAnchor(formatAnchor(anchor)) === canonical;
  }) || null;
};

const mergeAnchors = (current: string[], incoming: string[]): string[] => {
  const merged: string[] = [];
  for (const anchor of [...current, ...incoming]) {
    if (!anchor || merged.includes(anchor)) {
      continue;
    }
    merged.push(anchor);
  }
  return merged;
};

const parseUploadedAnchors = (rawText: string): string[] => {
  const text = rawText.trim();
  if (!text) {
    return [];
  }

  let tokens: string[] = [];
  try {
    const parsed = JSON.parse(text);
    if (Array.isArray(parsed)) {
      tokens = parsed.map((item) => String(item));
    } else if (parsed && typeof parsed === 'object') {
      const obj = parsed as Record<string, unknown>;
      const anchorList = obj.anchors ?? obj.selectedAnchors ?? obj.selected_anchors;
      if (Array.isArray(anchorList)) {
        tokens = anchorList.map((item) => String(item));
      }
    }
  } catch {
    tokens = text.split(/[\n,;]+/);
  }

  if (tokens.length === 0) {
    tokens = text.split(/[\n,;]+/);
  }

  return tokens
    .map((token) => resolveAnchor(token))
    .filter((anchor): anchor is string => Boolean(anchor));
};

const SettingsBar: React.FC<SettingsBarProps> = ({ config, onChange }) => {
  const targetLabel = config.engine.includes('Reverse') ? 'English' : 'Zyntalic';
  const anchorFileInputRef = React.useRef<HTMLInputElement>(null);
  const [anchorToAdd, setAnchorToAdd] = React.useState('');
  const [anchorStatus, setAnchorStatus] = React.useState<string | null>(null);

  const availableAnchors = ANCHORS.filter((anchor) => !config.selectedAnchors.includes(anchor));

  const syncAnchorSelection = (selectedAnchors: string[], anchorMode = config.anchorMode) => {
    const uniqueAnchors = mergeAnchors([], selectedAnchors);
    onChange({
      anchorMode,
      selectedAnchors: uniqueAnchors,
      ...(anchorMode === 'manual' ? deriveLegacyFrames(uniqueAnchors) : { frameA: '', frameB: '' }),
    });
  };

  const addAnchor = () => {
    const resolved = resolveAnchor(anchorToAdd);
    if (!resolved) {
      return;
    }
    syncAnchorSelection(mergeAnchors(config.selectedAnchors, [resolved]), 'manual');
    setAnchorToAdd('');
    setAnchorStatus(`${formatAnchor(resolved)} added.`);
  };

  const removeAnchor = (anchor: string) => {
    syncAnchorSelection(config.selectedAnchors.filter((item) => item !== anchor), config.anchorMode);
    setAnchorStatus(`${formatAnchor(anchor)} removed.`);
  };

  const handleAnchorModeChange = (mode: AnchorMode) => {
    onChange({
      anchorMode: mode,
      ...(mode === 'manual' ? deriveLegacyFrames(config.selectedAnchors) : { frameA: '', frameB: '' }),
    });
    setAnchorStatus(mode === 'neutral' ? 'Anchor bias disabled.' : null);
  };

  const triggerAnchorUpload = () => {
    anchorFileInputRef.current?.click();
  };

  const handleAnchorUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = (loadEvent) => {
      const rawText = String(loadEvent.target?.result || '');
      const parsedAnchors = parseUploadedAnchors(rawText);
      if (parsedAnchors.length === 0) {
        setAnchorStatus('No valid anchors found in upload.');
        return;
      }
      syncAnchorSelection(mergeAnchors(config.selectedAnchors, parsedAnchors), 'manual');
      setAnchorStatus(`${parsedAnchors.length} anchor${parsedAnchors.length === 1 ? '' : 's'} imported.`);
    };
    reader.onerror = () => {
      setAnchorStatus('Failed to read anchor upload.');
    };
    reader.readAsText(file);
    event.target.value = '';
  };

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
        <label className="text-xs font-bold text-slate-400 uppercase tracking-widest block">Anchor Control</label>
        <div className="space-y-3">
          <div className="space-y-1">
            <span className="text-[10px] text-slate-500 uppercase ml-1">Strategy</span>
            <select
              value={config.anchorMode}
              onChange={(e) => handleAnchorModeChange(e.target.value as AnchorMode)}
              className={selectClassName}
            >
              {ANCHOR_MODES.map((mode) => (
                <option key={mode.value} value={mode.value}>{mode.label}</option>
              ))}
            </select>
            <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500">
              {ANCHOR_MODES.find((mode) => mode.value === config.anchorMode)?.description}
            </p>
          </div>

          {config.anchorMode === 'manual' && (
            <div className="space-y-3 rounded-xl border border-slate-800/80 bg-slate-950/50 p-4">
              <div className="space-y-1">
                <span className="text-[10px] text-slate-500 uppercase ml-1">Add Anchor</span>
                <div className="flex gap-2">
                  <select
                    value={anchorToAdd}
                    onChange={(e) => setAnchorToAdd(e.target.value)}
                    className={`${selectClassName} flex-1`}
                  >
                    <option value="">Select anchor</option>
                    {availableAnchors.map((anchor) => (
                      <option key={`manual-${anchor}`} value={anchor}>{formatAnchor(anchor)}</option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={addAnchor}
                    disabled={!anchorToAdd}
                    className="rounded-lg border border-indigo-500/40 bg-indigo-500/10 px-3 py-2 text-xs font-bold uppercase tracking-[0.18em] text-indigo-200 transition-colors hover:bg-indigo-500/20 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Add
                  </button>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {config.selectedAnchors.length > 0 ? config.selectedAnchors.map((anchor) => (
                  <button
                    key={`chip-${anchor}`}
                    type="button"
                    onClick={() => removeAnchor(anchor)}
                    className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-cyan-200 transition-colors hover:bg-cyan-500/20"
                    title="Remove anchor"
                  >
                    {formatAnchor(anchor)} ×
                  </button>
                )) : (
                  <div className="text-[10px] uppercase tracking-[0.16em] text-slate-500">
                    No anchors selected.
                  </div>
                )}
              </div>

              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={triggerAnchorUpload}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-300 transition-colors hover:border-cyan-500/40 hover:text-cyan-200"
                >
                  Upload Anchor List
                </button>
                <button
                  type="button"
                  onClick={() => {
                    syncAnchorSelection([], 'manual');
                    setAnchorStatus('Manual anchors cleared.');
                  }}
                  disabled={config.selectedAnchors.length === 0}
                  className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-300 transition-colors hover:border-rose-500/40 hover:text-rose-200 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Clear
                </button>
              </div>

              <input
                ref={anchorFileInputRef}
                type="file"
                accept=".txt,.json"
                onChange={handleAnchorUpload}
                className="hidden"
              />

              <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500">
                Upload a `.txt` or `.json` file containing known anchor ids or names.
              </p>

              {anchorStatus && (
                <div className="text-[10px] uppercase tracking-[0.16em] text-slate-400">
                  {anchorStatus}
                </div>
              )}
            </div>
          )}

          {config.anchorMode === 'neutral' && (
            <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500">
              Neutral mode uses the base lexicon only and suppresses automatic anchor inference.
            </p>
          )}

          {config.anchorMode === 'auto' && (
            <p className="text-[10px] uppercase tracking-[0.16em] text-slate-500">
              Auto mode infers resonance from the source but does not lock the output to a manual anchor set.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default SettingsBar;
