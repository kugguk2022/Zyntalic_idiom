import React, { useEffect, useMemo, useRef, useState } from 'react';
import { TranslationConfig, TranslationEngine, TranslationResult } from './types';
import { performTranslation } from './services/apiService';
import SettingsBar from './components/SettingsBar';

const DEMOS = [
  {
    source: 'Time flows like water',
    target: '과먦톕 췃ńęn챿 ła괽쮄 믔뚿숦',
  },
  {
    source: 'Knowledge is power',
    target: '렺zę쀞듼 듡힞ć 뤻펡쉽ć',
  },
  {
    source: 'Beautiful birds sing',
    target: '텋젵뫰퍆 깏꽂번 mopjiću',
  },
  {
    source: 'Hope springs eternal',
    target: '븩rązcuc 쐬뷽뮪꿼 ńo쇍곗쮯',
  },
];

const GLYPHS = Array.from('⟡◊⌁∿∆∴·⟢⟣ʒŋłćńęą쥂챿숦듼렺힞쀞');

const clamp = (value: number, min = 0, max = 1) => Math.max(min, Math.min(max, value));

const hashIndex = (index: number, salt: number) => {
  let x = (index + 1) * 2654435761 + salt * 2246822519;
  x ^= x >>> 15;
  x = Math.imul(x, 3266489917);
  x ^= x >>> 16;
  return Math.abs(x >>> 0);
};

const morphText = (source: string, target: string, progress: number, salt: number): string => {
  const from = Array.from(source);
  const to = Array.from(target);
  const length = Math.max(from.length, to.length);
  const p = clamp(progress);

  return Array.from({ length }, (_, index) => {
    const revealAt = 0.08 + ((hashIndex(index, salt) % 1000) / 1000) * 0.78;
    const sourceChar = from[index] ?? ' ';
    const targetChar = to[index] ?? '';

    if (p >= revealAt) return targetChar;
    if (p < revealAt - 0.16) return sourceChar;

    const glyphIndex = (hashIndex(index + Math.floor(p * 41), salt + 7) + index) % GLYPHS.length;
    return GLYPHS[glyphIndex];
  }).join('');
};

const counterSurface = (target: string): string => {
  const chars = Array.from(target);
  return chars.map((char, index) => {
    if (/\s/.test(char)) return char;
    if (index % 5 !== 2) return char;
    return GLYPHS[hashIndex(index, 19) % GLYPHS.length];
  }).join('');
};

const agreementScore = (a: string, b: string): number => {
  const left = Array.from(a);
  const right = Array.from(b);
  const length = Math.max(left.length, right.length);
  if (length === 0) return 100;
  let matches = 0;
  for (let index = 0; index < length; index += 1) {
    if ((left[index] ?? '') === (right[index] ?? '')) matches += 1;
  }
  return Math.round((matches / length) * 100);
};

const App: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [primaryResult, setPrimaryResult] = useState<TranslationResult | null>(null);
  const [secondaryResult, setSecondaryResult] = useState<TranslationResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<'demo' | 'live'>('demo');
  const [demoIndex, setDemoIndex] = useState(0);
  const [phase, setPhase] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [config, setConfig] = useState<TranslationConfig>({
    engine: TranslationEngine.SEMANTIC,
    mirror: 0.3,
    sourceLang: 'Auto-detect',
    targetLang: 'Zyntalic',
    evidentiality: 'direct',
    register: 'formal',
    dialect: 'standard',
    anchorMode: 'auto',
    selectedAnchors: [],
    frameA: '',
    frameB: '',
  });

  useEffect(() => {
    if (isPaused) return undefined;

    const interval = window.setInterval(() => {
      setPhase((current) => {
        if (mode === 'live') return Math.min(100, current + 2.4);
        if (current >= 100) {
          setDemoIndex((index) => (index + 1) % DEMOS.length);
          return 0;
        }
        return current + 1.45;
      });
    }, 70);

    return () => window.clearInterval(interval);
  }, [isPaused, mode]);

  const demo = DEMOS[demoIndex];
  const source = mode === 'live' ? inputText : demo.source;
  const primaryTarget = mode === 'live'
    ? (primaryResult?.text || source)
    : demo.target;
  const secondaryTarget = mode === 'live'
    ? (secondaryResult?.text || primaryTarget)
    : counterSurface(demo.target);

  const normalizedPhase = phase / 100;
  const pathAProgress = clamp((normalizedPhase - 0.08) / 0.58);
  const pathBProgress = clamp((normalizedPhase - 0.16) / 0.58);
  const convergenceProgress = clamp((normalizedPhase - 0.62) / 0.32);

  const traceA = useMemo(
    () => morphText(source, primaryTarget, pathAProgress, 11),
    [source, primaryTarget, pathAProgress],
  );
  const traceB = useMemo(
    () => morphText(source, secondaryTarget, pathBProgress, 29),
    [source, secondaryTarget, pathBProgress],
  );
  const finalSurface = useMemo(
    () => morphText(source, primaryTarget, convergenceProgress, 47),
    [source, primaryTarget, convergenceProgress],
  );

  const agreement = agreementScore(primaryTarget, secondaryTarget);
  const readback = mode === 'live' ? primaryResult?.mirrorText : undefined;
  const latency = mode === 'live'
    ? Math.max(primaryResult?.latency || 0, secondaryResult?.latency || 0)
    : null;
  const traceLabelA = mode === 'live' ? config.engine : 'semantic path';
  const traceLabelB = mode === 'live'
    ? (config.engine === TranslationEngine.SEMANTIC ? TranslationEngine.NEURAL : TranslationEngine.SEMANTIC)
    : 'counter path';

  const challengerConfig = (): TranslationConfig => ({
    ...config,
    engine: config.engine === TranslationEngine.SEMANTIC
      ? TranslationEngine.NEURAL
      : TranslationEngine.SEMANTIC,
    mirror: clamp(config.mirror + 0.12),
  });

  const handleTranslate = async () => {
    const text = inputText.trim();
    if (!text) return;

    setIsProcessing(true);
    setError(null);
    setPrimaryResult(null);
    setSecondaryResult(null);

    try {
      const [primary, challenger] = await Promise.allSettled([
        performTranslation(text, config),
        performTranslation(text, challengerConfig()),
      ]);

      if (primary.status === 'rejected' && challenger.status === 'rejected') {
        const reasonA = primary.reason instanceof Error ? primary.reason.message : String(primary.reason);
        const reasonB = challenger.reason instanceof Error ? challenger.reason.message : String(challenger.reason);
        throw new Error(`Both traces failed. A: ${reasonA} B: ${reasonB}`);
      }

      const resolvedPrimary = primary.status === 'fulfilled'
        ? primary.value
        : challenger.status === 'fulfilled'
          ? challenger.value
          : null;
      const resolvedSecondary = challenger.status === 'fulfilled'
        ? challenger.value
        : resolvedPrimary;

      setPrimaryResult(resolvedPrimary);
      setSecondaryResult(resolvedSecondary);
      setMode('live');
      setPhase(0);
      setIsPaused(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Dual trace failed.');
    } finally {
      setIsProcessing(false);
    }
  };

  const returnToDemo = () => {
    setMode('demo');
    setPhase(0);
    setIsPaused(false);
    setError(null);
  };

  const copyResult = async () => {
    if (!primaryResult?.text) return;
    await navigator.clipboard.writeText(primaryResult.text);
  };

  const downloadResult = () => {
    if (!primaryResult?.text) return;
    const blob = new Blob([primaryResult.text], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'zyntalic-dual-trace.txt';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const extension = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!['.txt', '.md'].includes(extension)) {
      setError('This polished preview accepts TXT or MD directly. PDF extraction remains available through the API.');
      return;
    }

    const reader = new FileReader();
    reader.onload = (readEvent) => {
      setInputText(String(readEvent.target?.result || ''));
      setError(null);
    };
    reader.onerror = () => setError('Could not read that file.');
    reader.readAsText(file);
  };

  const frameNames = primaryResult?.sidecar?.frames?.map((frame) => frame.anchor).slice(0, 3) || [];

  return (
    <div className="min-h-screen text-slate-100 selection:bg-cyan-300/20">
      <header className="sticky top-0 z-50 border-b border-white/5 bg-[#05070d]/78 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="absolute inset-0 rounded-xl bg-cyan-300/20 blur-lg" />
              <img src="/favicon.svg" alt="Zyntalic" className="relative h-9 w-9 rounded-xl" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm font-semibold tracking-[0.18em] text-white">ZYNTALIC</span>
                <span className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-2 py-0.5 text-[9px] font-bold uppercase tracking-[0.2em] text-cyan-200">
                  Dual trace
                </span>
              </div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-slate-600">Synthetic language engine</p>
            </div>
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-500">
            <span className="hidden sm:inline">Public transformation traces · not private chain-of-thought</span>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.035] px-3 py-1.5 text-slate-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_12px_rgba(52,211,153,.75)]" />
              live
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 pb-20 pt-10 sm:px-6 sm:pt-14">
        <section className="mb-10 grid gap-8 lg:grid-cols-[1.1fr_.9fr] lg:items-end">
          <div>
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.035] px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.24em] text-slate-400">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-300" />
              plaintext → dual transform → Zyntalic
            </div>
            <h1 className="max-w-4xl text-4xl font-semibold tracking-[-0.04em] text-white sm:text-5xl lg:text-6xl">
              Watch language split,
              <span className="text-slate-500"> disagree, and converge.</span>
            </h1>
          </div>
          <p className="max-w-xl text-sm leading-6 text-slate-400 lg:justify-self-end lg:text-base">
            The interface now demonstrates the engine before asking anything from the user. Two deterministic public traces evolve in parallel, then settle on the generated surface.
          </p>
        </section>

        <section className="zy-theatre overflow-hidden rounded-[30px] border border-white/10 bg-[#080b13]/86 shadow-[0_40px_100px_rgba(0,0,0,.42)]">
          <div className="flex flex-col gap-4 border-b border-white/5 px-5 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-7">
            <div className="flex items-center gap-3">
              <span className={`rounded-full px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.22em] ${mode === 'live' ? 'bg-emerald-300/10 text-emerald-200 ring-1 ring-emerald-300/20' : 'bg-white/5 text-slate-400 ring-1 ring-white/10'}`}>
                {mode === 'live' ? 'live run' : 'autoplay demo'}
              </span>
              <span className="text-xs text-slate-600">{mode === 'demo' ? `sequence 0${demoIndex + 1}` : 'two API passes'}</span>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setIsPaused((paused) => !paused)}
                className="rounded-full border border-white/10 bg-white/[0.035] px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:border-white/20 hover:bg-white/[0.06]"
              >
                {isPaused ? 'Play' : 'Pause'}
              </button>
              {mode === 'live' && (
                <button
                  type="button"
                  onClick={returnToDemo}
                  className="rounded-full border border-white/10 bg-white/[0.035] px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:border-white/20 hover:bg-white/[0.06]"
                >
                  Demo loop
                </button>
              )}
            </div>
          </div>

          <div className="relative p-5 sm:p-7 lg:p-9">
            <div className="zy-grid absolute inset-0 opacity-35" />
            <div className="relative space-y-6">
              <div className="rounded-2xl border border-white/8 bg-black/20 p-5 sm:p-6">
                <div className="mb-3 flex items-center justify-between gap-4">
                  <span className="text-[10px] font-bold uppercase tracking-[0.24em] text-slate-500">Plaintext</span>
                  <span className="mono text-[10px] text-slate-700">SOURCE / UTF-8</span>
                </div>
                <div className="mono min-h-12 text-lg leading-8 text-slate-200 sm:text-xl">{source || 'Awaiting input…'}</div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <article className="group relative overflow-hidden rounded-2xl border border-cyan-300/15 bg-cyan-300/[0.035] p-5 sm:p-6">
                  <div className="zy-scan absolute inset-y-0 w-24 bg-gradient-to-r from-transparent via-cyan-200/[0.06] to-transparent" style={{ left: `${Math.max(-20, pathAProgress * 112 - 10)}%` }} />
                  <div className="relative">
                    <div className="mb-4 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full border border-cyan-300/20 bg-cyan-300/10 text-[10px] font-bold text-cyan-200">A</span>
                        <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-cyan-200/80">semantic trace</span>
                      </div>
                      <span className="max-w-[45%] truncate text-[10px] text-slate-600">{traceLabelA}</span>
                    </div>
                    <div className="mono min-h-28 whitespace-pre-wrap break-words text-base leading-7 text-slate-200 sm:text-lg">
                      {traceA || '…'}
                    </div>
                  </div>
                </article>

                <article className="group relative overflow-hidden rounded-2xl border border-violet-300/15 bg-violet-300/[0.03] p-5 sm:p-6">
                  <div className="zy-scan absolute inset-y-0 w-24 bg-gradient-to-r from-transparent via-violet-200/[0.06] to-transparent" style={{ right: `${Math.max(-20, pathBProgress * 112 - 10)}%` }} />
                  <div className="relative">
                    <div className="mb-4 flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full border border-violet-300/20 bg-violet-300/10 text-[10px] font-bold text-violet-200">B</span>
                        <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-violet-200/80">challenger trace</span>
                      </div>
                      <span className="max-w-[45%] truncate text-[10px] text-slate-600">{traceLabelB}</span>
                    </div>
                    <div className="mono min-h-28 whitespace-pre-wrap break-words text-base leading-7 text-slate-200 sm:text-lg">
                      {traceB || '…'}
                    </div>
                  </div>
                </article>
              </div>

              <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.035] p-5 sm:p-6">
                <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-cyan-200/50 to-transparent" />
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <span className="relative flex h-7 w-7 items-center justify-center rounded-full border border-white/10 bg-white/5">
                      <span className="absolute h-2 w-2 animate-ping rounded-full bg-cyan-300/50" />
                      <span className="relative h-2 w-2 rounded-full bg-cyan-200" />
                    </span>
                    <div>
                      <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-300">Converged surface</div>
                      <div className="text-[10px] text-slate-600">primary engine output</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-[10px] text-slate-500">
                    <span className="rounded-full border border-white/8 bg-black/20 px-2 py-1">surface overlap {agreement}%</span>
                    {latency !== null && latency > 0 && (
                      <span className="rounded-full border border-white/8 bg-black/20 px-2 py-1">{latency} ms</span>
                    )}
                  </div>
                </div>

                <div className="mono min-h-20 whitespace-pre-wrap break-words text-xl leading-9 text-white sm:text-2xl">
                  {finalSurface || '…'}
                </div>

                {readback && phase >= 86 && (
                  <div className="mt-5 border-t border-white/5 pt-4">
                    <div className="mb-2 text-[9px] font-bold uppercase tracking-[0.22em] text-slate-600">Engine readback</div>
                    <div className="text-sm leading-6 text-slate-400">{readback}</div>
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3">
                <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-300/70 via-violet-300/70 to-white/70 transition-[width] duration-100"
                    style={{ width: `${Math.min(100, phase)}%` }}
                  />
                </div>
                <span className="mono w-10 text-right text-[10px] text-slate-600">{Math.round(Math.min(100, phase))}%</span>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-8 grid gap-6 lg:grid-cols-[1fr_320px]">
          <div className="rounded-[26px] border border-white/10 bg-[#080b13]/72 p-5 sm:p-7">
            <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-[0.24em] text-slate-600">Your turn</span>
                <h2 className="mt-1 text-xl font-semibold tracking-tight text-white">Feed the duel a sentence.</h2>
              </div>
              <span className="text-xs text-slate-600">Ctrl / ⌘ + Enter to run</span>
            </div>

            <textarea
              value={inputText}
              onChange={(event) => setInputText(event.target.value)}
              onKeyDown={(event) => {
                if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
                  event.preventDefault();
                  void handleTranslate();
                }
              }}
              placeholder="A new idea enters as ordinary language…"
              className="mono min-h-36 w-full resize-y rounded-2xl border border-white/10 bg-black/20 px-4 py-4 text-base leading-7 text-slate-200 outline-none transition placeholder:text-slate-700 focus:border-cyan-300/30 focus:bg-black/30"
            />

            {error && (
              <div className="mt-4 rounded-xl border border-rose-300/15 bg-rose-300/[0.05] px-4 py-3 text-sm leading-5 text-rose-200">
                {error}
              </div>
            )}

            <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="rounded-xl border border-white/10 bg-white/[0.035] px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:border-white/20 hover:bg-white/[0.06]"
                >
                  Open TXT / MD
                </button>
                <input ref={fileInputRef} type="file" accept=".txt,.md" className="hidden" onChange={handleFileUpload} />
                {primaryResult && (
                  <>
                    <button
                      type="button"
                      onClick={() => void copyResult()}
                      className="rounded-xl border border-white/10 bg-white/[0.035] px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:border-white/20 hover:bg-white/[0.06]"
                    >
                      Copy surface
                    </button>
                    <button
                      type="button"
                      onClick={downloadResult}
                      className="rounded-xl border border-white/10 bg-white/[0.035] px-4 py-2.5 text-sm font-medium text-slate-300 transition hover:border-white/20 hover:bg-white/[0.06]"
                    >
                      Download
                    </button>
                  </>
                )}
              </div>

              <button
                type="button"
                onClick={() => void handleTranslate()}
                disabled={isProcessing || !inputText.trim()}
                className="group inline-flex min-w-44 items-center justify-center gap-3 rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-slate-950 transition hover:bg-cyan-100 disabled:cursor-not-allowed disabled:opacity-35"
              >
                <span>{isProcessing ? 'Splitting traces…' : 'Run dual trace'}</span>
                <span className={`text-base transition-transform ${isProcessing ? 'animate-pulse' : 'group-hover:translate-x-0.5'}`}>→</span>
              </button>
            </div>
          </div>

          <aside className="space-y-4">
            <div className="rounded-[26px] border border-white/10 bg-[#080b13]/72 p-5">
              <div className="mb-4 text-[10px] font-bold uppercase tracking-[0.24em] text-slate-600">Run telemetry</div>
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-slate-500">Mode</span>
                  <span className="text-slate-200">{mode === 'live' ? 'Dual API' : 'Autoplay'}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-slate-500">Trace passes</span>
                  <span className="mono text-slate-200">2</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-slate-500">Mirror rate</span>
                  <span className="mono text-slate-200">{config.mirror.toFixed(2)}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span className="text-slate-500">Surface overlap</span>
                  <span className="mono text-slate-200">{agreement}%</span>
                </div>
              </div>

              {frameNames.length > 0 && (
                <div className="mt-5 border-t border-white/5 pt-4">
                  <div className="mb-2 text-[9px] font-bold uppercase tracking-[0.2em] text-slate-600">Active frames</div>
                  <div className="flex flex-wrap gap-1.5">
                    {frameNames.map((frame) => (
                      <span key={frame} className="rounded-full border border-cyan-300/10 bg-cyan-300/[0.04] px-2 py-1 text-[10px] text-cyan-100/70">
                        {frame.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <details className="group rounded-[26px] border border-white/10 bg-[#080b13]/72 p-5">
              <summary className="flex cursor-pointer list-none items-center justify-between text-sm font-medium text-slate-300">
                Engine controls
                <span className="text-slate-600 transition group-open:rotate-45">＋</span>
              </summary>
              <div className="mt-5 border-t border-white/5 pt-5">
                <SettingsBar config={config} onChange={(update) => setConfig((current) => ({ ...current, ...update }))} />
              </div>
            </details>
          </aside>
        </section>

        <section className="mt-12 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-5">
            <div className="mb-2 text-[9px] font-bold uppercase tracking-[0.22em] text-cyan-200/60">01 · observe</div>
            <p className="text-sm leading-6 text-slate-400">The product explains itself in motion before the first click.</p>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-5">
            <div className="mb-2 text-[9px] font-bold uppercase tracking-[0.22em] text-violet-200/60">02 · diverge</div>
            <p className="text-sm leading-6 text-slate-400">A semantic path and a challenger path produce inspectable public surfaces.</p>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/[0.025] p-5">
            <div className="mb-2 text-[9px] font-bold uppercase tracking-[0.22em] text-white/50">03 · converge</div>
            <p className="text-sm leading-6 text-slate-400">The primary Zyntalic result settles only after the duel has been shown.</p>
          </div>
        </section>
      </main>

      <footer className="border-t border-white/5 bg-black/20 py-7">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 text-xs text-slate-600 sm:px-6 md:flex-row md:items-center md:justify-between">
          <span>Zyntalic Flow · experimental synthetic-language research interface</span>
          <span className="mono">UI / dual-trace cinematic prototype</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
