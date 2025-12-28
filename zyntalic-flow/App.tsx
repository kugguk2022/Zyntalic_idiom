
import React, { useState, useCallback, useRef } from 'react';
import { TranslationEngine, TranslationConfig, TranslationResult } from './types';
import { performTranslation } from './services/apiService';
import SettingsBar from './components/SettingsBar';

const App: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [outputResult, setOutputResult] = useState<TranslationResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [config, setConfig] = useState<TranslationConfig>({
    engine: TranslationEngine.SEMANTIC,
    mirror: 0.3,  // Lower value shows more Zyntalic vocabulary
    sourceLang: 'Auto-detect',
    targetLang: 'English'
  });

  const handleTranslate = async () => {
    if (!inputText.trim()) return;
    
    setIsProcessing(true);
    setError(null);
    try {
      const result = await performTranslation(inputText, config);
      setOutputResult(result);
      // Auto-export the result
      downloadText(result.text, 'zyntalic_export.txt');
    } catch (err: any) {
      setError(err.message || 'Transmission error detected.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Check file type
      const validTypes = ['.txt', '.md', '.pdf'];
      const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
      
      if (!validTypes.includes(fileExt)) {
        setError(`Invalid file type. Please upload TXT, MD, or PDF files.`);
        return;
      }
      
      // Handle text files directly
      if (fileExt === '.txt' || fileExt === '.md') {
        const reader = new FileReader();
        reader.onload = (ev) => {
          const text = ev.target?.result as string;
          setInputText(text);
        };
        reader.onerror = () => {
          setError('Failed to read file. Please try again.');
        };
        reader.readAsText(file);
      } else if (fileExt === '.pdf') {
        // Handle PDF via backend API
        const formData = new FormData();
        formData.append('file', file);
        
        setIsProcessing(true);
        setError(null);
        
        fetch('/upload', {
          method: 'POST',
          body: formData,
        })
          .then(response => {
            if (!response.ok) {
              return response.json().then(err => {
                throw new Error(err.detail || 'Failed to process PDF');
              });
            }
            return response.json();
          })
          .then(data => {
            setInputText(data.text);
            setIsProcessing(false);
          })
          .catch(err => {
            setError(err.message || 'Failed to process PDF file.');
            setIsProcessing(false);
          });
      }
    }
  };

  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  const copyToClipboard = () => {
    if (outputResult) {
      navigator.clipboard.writeText(outputResult.text);
    }
  };

  const downloadText = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const exportVisible = () => {
    if (!outputResult) return;
    downloadText(outputResult.text, 'zyntalic_export.txt');
  };

  const exportZyntalicOnly = () => {
    if (!outputResult) return;
    const blocks = outputResult.text.split(/\n\s*\n/);
    const zOnly = blocks
      .map((block) => {
        const lines = block.split(/\n/);
        const arrow = lines.find((l) => l.trim().startsWith('→'));
        if (arrow) {
          return arrow.replace(/^.*→\s?/, '').trim();
        }
        // Fallback: if no arrow, return last line
        return lines[lines.length - 1]?.trim() || '';
      })
      .filter(Boolean)
      .join('\n');
    downloadText(zOnly, 'zyntalic_only.txt');
  };

  return (
    <div className="min-h-screen flex flex-col text-slate-200 selection:bg-indigo-500/30">
      {/* Header */}
      <header className="border-b border-slate-800/60 bg-slate-950/80 backdrop-blur-md sticky top-0 z-50 transition-colors duration-300">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-4 group cursor-default">
            <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition-all duration-300 group-hover:scale-105 group-hover:rotate-3">
              <svg viewBox="0 0 24 24" className="w-6 h-6 text-white fill-current">
                <path d="M12 2L4.5 20.29l.71.71L12 18l6.79 3 .71-.71L12 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight text-white transition-colors group-hover:text-indigo-400">Zyntalic Flow</h1>
              <p className="text-[10px] text-slate-500 font-medium uppercase tracking-[0.2em] -mt-1">Deterministic Semantic Engine</p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="hidden md:flex flex-col items-end">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-sm shadow-green-500/50"></span>
                <span className="text-xs font-semibold text-slate-400">System Online</span>
              </div>
              <span className="text-[10px] text-slate-600 mono">v0.3-beta.build_812</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto w-full px-6 py-10 grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Settings */}
        <aside className="lg:col-span-3 space-y-6">
          <SettingsBar config={config} onChange={(upd) => setConfig(prev => ({ ...prev, ...upd }))} />
          
          <div className="bg-slate-900/30 border border-slate-800/50 p-6 rounded-2xl hidden lg:block hover:bg-slate-900/40 transition-colors duration-300">
            <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-4">Diagnostics</h3>
            <div className="space-y-3">
              <div className="flex justify-between text-xs group">
                <span className="text-slate-500 group-hover:text-slate-400 transition-colors">Latency</span>
                <span className="mono text-slate-300 tabular-nums">{outputResult?.latency || '--'}ms</span>
              </div>
              <div className="flex justify-between text-xs group">
                <span className="text-slate-500 group-hover:text-slate-400 transition-colors">Confidence</span>
                <span className="mono text-slate-300 tabular-nums">{(outputResult?.confidence || 0 * 100).toFixed(1)}%</span>
              </div>
              <div className="flex justify-between text-xs group">
                <span className="text-slate-500 group-hover:text-slate-400 transition-colors">Entropy</span>
                <span className="mono text-slate-300 tabular-nums">{(1 - config.mirror).toFixed(2)}</span>
              </div>
            </div>
          </div>
        </aside>

        {/* Right: Workspace */}
        <div className="lg:col-span-9 space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 min-h-[500px]">
            {/* Source Card */}
            <div className="flex flex-col bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl transition-all duration-500 hover:border-indigo-500/30 hover:shadow-indigo-500/5 group">
              <div className="bg-slate-800/30 px-6 py-4 flex justify-between items-center group-hover:bg-slate-800/50 transition-colors">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Source Input</span>
                <div className="flex items-center gap-2">
                  <button 
                    onClick={triggerFileUpload}
                    className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-slate-700/50 rounded-md transition-all duration-200 active:scale-90"
                    title="Upload File"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                  </button>
                  <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept=".txt,.md,.pdf" />
                  <button 
                    onClick={() => {
                      setInputText('');
                      setOutputResult(null);
                    }}
                    className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-md transition-all duration-200 active:scale-90"
                    title="Clear"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
              <textarea 
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Initialize semantic stream by typing or dragging a file..."
                className="flex-1 bg-transparent p-6 text-lg leading-relaxed focus:outline-none resize-none placeholder:text-slate-700 mono transition-all duration-300 focus:placeholder:opacity-50"
              />
            </div>

            {/* Target Card */}
            <div className="flex flex-col bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-2xl transition-all duration-500 hover:border-indigo-500/30 hover:shadow-indigo-500/5 group relative">
              <div className="bg-slate-800/30 px-6 py-4 flex justify-between items-center group-hover:bg-slate-800/50 transition-colors">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">Target Surface</span>
                <div className="flex items-center gap-2">
                  <button 
                    onClick={copyToClipboard}
                    disabled={!outputResult}
                    className="p-1.5 text-slate-400 hover:text-indigo-400 hover:bg-slate-700/50 rounded-md transition-all duration-200 disabled:opacity-30 active:scale-90"
                    title="Copy Results"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m-3 8h3m-3 4h3m-6-4h.01M9 16h.01" />
                    </svg>
                  </button>
                  <button
                    onClick={exportVisible}
                    disabled={!outputResult}
                    className="px-3 py-1 text-xs font-semibold rounded-md border border-slate-700 text-slate-300 hover:border-indigo-500 hover:text-indigo-300 hover:bg-indigo-500/10 transition-all duration-200 disabled:opacity-30"
                    title="Export exactly what is shown"
                  >
                    Export shown
                  </button>
                  <button
                    onClick={exportZyntalicOnly}
                    disabled={!outputResult}
                    className="px-3 py-1 text-xs font-semibold rounded-md border border-slate-700 text-slate-300 hover:border-emerald-500 hover:text-emerald-200 hover:bg-emerald-500/10 transition-all duration-200 disabled:opacity-30"
                    title="Export Zyntalic text only"
                  >
                    Export Zyntalic
                  </button>
                </div>
              </div>
              <div className="flex-1 p-6 text-lg leading-relaxed mono whitespace-pre-wrap overflow-y-auto">
                {isProcessing ? (
                  <div className="flex flex-col items-center justify-center h-full gap-4 text-slate-500 animate-fade-in-up">
                    <div className="w-12 h-1 bg-indigo-500/10 rounded-full relative overflow-hidden">
                      <div className="absolute inset-y-0 left-0 bg-indigo-500 w-1/2 animate-[shimmer_1.5s_infinite] shadow-[0_0_10px_rgba(99,102,241,0.8)]"></div>
                    </div>
                    <span className="text-sm font-medium tracking-wide">Syncing Neural Context...</span>
                  </div>
                ) : outputResult ? (
                  <div className="text-slate-200 animate-fade-in-up">
                    {outputResult.text}
                  </div>
                ) : (
                  <span className="text-slate-700 italic transition-opacity duration-500">Waiting for translation output...</span>
                )}
                {error && (
                  <div className="text-red-400 text-sm mt-4 p-4 bg-red-400/5 border border-red-400/20 rounded-lg flex justify-between items-start gap-3 animate-fade-in-up">
                    <span>{error}</span>
                    <button 
                      onClick={() => setError(null)}
                      className="p-1 hover:bg-red-400/10 rounded transition-colors shrink-0"
                      aria-label="Clear error"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Action Footer */}
          <div className="flex flex-col md:flex-row items-center justify-between gap-6 p-2">
            <div className="flex items-center gap-6 text-slate-500">
              <div className="flex items-center gap-2 group cursor-help">
                <div className="w-3 h-3 border-2 border-slate-700 rounded-full flex items-center justify-center group-hover:border-indigo-500 transition-colors duration-300">
                  <div className="w-1 h-1 bg-slate-500 group-hover:bg-indigo-500 rounded-full"></div>
                </div>
                <span className="text-xs uppercase font-bold tracking-widest group-hover:text-slate-400 transition-colors">Secure Transmission</span>
              </div>
              <div className="flex items-center gap-2 group cursor-help">
                 <svg className="w-4 h-4 group-hover:text-indigo-500 transition-colors duration-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                 </svg>
                 <span className="text-xs uppercase font-bold tracking-widest group-hover:text-slate-400 transition-colors">Encrypted flow</span>
              </div>
            </div>

            <button 
              onClick={handleTranslate}
              disabled={isProcessing || !inputText.trim()}
              className="group relative inline-flex items-center gap-3 px-10 py-5 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 disabled:opacity-50 text-white font-bold rounded-2xl shadow-xl shadow-indigo-600/20 transition-all duration-300 active:scale-[0.98] hover:-translate-y-1 overflow-hidden"
            >
              <span className="relative z-10">{isProcessing ? 'Processing...' : 'Initialize Flow'}</span>
              <svg 
                className={`w-5 h-5 relative z-10 transition-transform duration-300 ${isProcessing ? 'animate-spin' : 'group-hover:translate-x-1'}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
              <div className="absolute inset-0 bg-gradient-to-r from-indigo-400/0 via-white/10 to-indigo-400/0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-in-out"></div>
              <div className="absolute -inset-1 bg-indigo-500/20 rounded-2xl blur opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            </button>
          </div>
        </div>
      </main>

      <footer className="py-8 border-t border-slate-800/60 bg-slate-950 mt-12 transition-all duration-300">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-slate-600 text-xs">
            Powered by <span className="text-slate-400 font-bold hover:text-indigo-400 transition-colors cursor-default">Zyntalic Engine v0.3 (Experimental)</span>. 
            Proprietary Semantic Mapping Architecture.
          </p>
          <div className="flex gap-8 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            <a href="#" className="hover:text-indigo-400 transition-all duration-200 relative group">
              Documentation
              <span className="absolute -bottom-1 left-0 w-0 h-px bg-indigo-500 transition-all duration-200 group-hover:w-full"></span>
            </a>
            <a href="#" className="hover:text-indigo-400 transition-all duration-200 relative group">
              Safety Protocols
              <span className="absolute -bottom-1 left-0 w-0 h-px bg-indigo-500 transition-all duration-200 group-hover:w-full"></span>
            </a>
            <a href="#" className="hover:text-indigo-400 transition-all duration-200 relative group">
              API Keys
              <span className="absolute -bottom-1 left-0 w-0 h-px bg-indigo-500 transition-all duration-200 group-hover:w-full"></span>
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
