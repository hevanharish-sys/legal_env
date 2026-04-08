import React, { useState, useRef, useEffect } from "react";
import { VideoBackground } from "./components/VideoBackground";
import {
  MicrophoneIcon,
  PaperclipIcon,
  SearchIcon,
  StarIcon,
  UpArrowIcon,
  DownloadIcon,
} from "./icons";

type TaskName = "easy" | "medium" | "hard";

type Observation = {
  clause: string;
  contract_type: string;
  jurisdiction: string;
};

type StepResponse = {
  observation: Observation;
  reward: { score: number };
  done: boolean;
  info: any;
};

type AnalysisResult = {
  id: number;
  clause: string;
  analysis: {
    risk_level: string;
    risk_type: string;
    rewrite: string;
    reason: string;
    explanation: string;
    impact: string;
    confidence: number;
    highlights_red: string[];
    highlights_yellow: string[];
    phrases: Record<string, string>;
  };
};

type DocumentReport = {
  filename: string;
  results: AnalysisResult[];
  stats: {
    score: number;
    high_risk_count: number;
    medium_risk_count: number;
    low_risk_count: number;
    distribution: { high: number; medium: number; low: number };
    top_risks: string[];
  };
};

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) || "";

function HighlightedText({ text, red, yellow, phrases }: { text: string; red: string[]; yellow: string[]; phrases: Record<string, string> }) {
  if (!red.length && !yellow.length) return <>{text}</>;

  const all = [...red, ...yellow].sort((a, b) => b.length - a.length);
  const regex = new RegExp(`(${all.map(h => h.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})`, "gi");
  const parts = text.split(regex);

  return (
    <>
      {parts.map((part, i) => {
        const isRed = red.some(h => h.toLowerCase() === part.toLowerCase());
        const isYellow = yellow.some(h => h.toLowerCase() === part.toLowerCase());
        const lowerPart = part.toLowerCase();
        const tooltip = Object.entries(phrases).find(([k]) => k.toLowerCase() === lowerPart)?.[1];

        if (isRed) return <span key={i} title={tooltip} className="bg-red-500/10 text-red-600 border-b-2 border-red-500/50 cursor-help px-0.5 rounded-sm font-bold">{part}</span>;
        if (isYellow) return <span key={i} title={tooltip} className="bg-yellow-500/10 text-yellow-700 border-b-2 border-yellow-500/50 cursor-help px-0.5 rounded-sm font-bold">{part}</span>;
        return part;
      })}
    </>
  );
}

function RiskHeatmap({ distribution }: { distribution: { high: number; medium: number; low: number } }) {
    return (
        <div className="w-full">
            <div className="flex justify-between text-[11px] font-bold uppercase tracking-wider text-black/40 mb-2">
                <span>Risk Exposure Heatmap</span>
                <span>{distribution.high}% High Intensity</span>
            </div>
            <div className="h-4 w-full bg-black/5 rounded-full overflow-hidden flex shadow-inner">
                <div 
                    className="h-full bg-red-500 transition-all duration-1000 ease-out relative group" 
                    style={{ width: `${distribution.high}%` }}
                >
                    <div className="opacity-0 group-hover:opacity-100 absolute inset-0 flex items-center justify-center text-[9px] text-white font-bold transition-opacity">HIGH</div>
                </div>
                <div 
                    className="h-full bg-yellow-400 transition-all duration-1000 delay-100 ease-out relative group" 
                    style={{ width: `${distribution.medium}%` }}
                >
                     <div className="opacity-0 group-hover:opacity-100 absolute inset-0 flex items-center justify-center text-[9px] text-yellow-900 font-bold transition-opacity">MED</div>
                </div>
                <div 
                    className="h-full bg-green-400 transition-all duration-1000 delay-200 ease-out relative group" 
                    style={{ width: `${distribution.low}%` }}
                >
                     <div className="opacity-0 group-hover:opacity-100 absolute inset-0 flex items-center justify-center text-[9px] text-green-900 font-bold transition-opacity">LOW</div>
                </div>
            </div>
        </div>
    );
}

export default function App() {
  const [question, setQuestion] = useState("");
  const [charCount, setCharCount] = useState(0);

  const [lastError, setLastError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<DocumentReport | null>(null);
  const [activeClause, setActiveClause] = useState<number | null>(null);
  const [visibleCount, setVisibleCount] = useState<number>(5);
  const [isDictating, setIsDictating] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  // Web Speech API Setup
  useEffect(() => {
    if (typeof window !== "undefined" && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)) {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = true;
        recognitionRef.current.interimResults = true;
        
        recognitionRef.current.onresult = (event: any) => {
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript + ' ';
                }
            }
            if (finalTranscript) {
                setQuestion(prev => {
                    const newText = prev + (prev.length > 0 && !prev.endsWith(' ') ? ' ' : '') + finalTranscript;
                    setCharCount(newText.length);
                    return newText;
                });
            }
        };

        recognitionRef.current.onerror = () => setIsDictating(false);
        recognitionRef.current.onend = () => setIsDictating(false);
    }
  }, []);

  const toggleDictation = () => {
      if (isDictating) {
          recognitionRef.current?.stop();
          setIsDictating(false);
      } else {
          try {
              recognitionRef.current?.start();
              setIsDictating(true);
          } catch(e) {
              console.error("Microphone access failed", e);
          }
      }
  };

  // Progressive Rendering Observer
  useEffect(() => {
      if (!report || visibleCount >= report.results.length) return;
      const observer = new IntersectionObserver((entries) => {
          if (entries[0].isIntersecting) setVisibleCount(prev => Math.min(prev + 5, report.results.length));
      }, { rootMargin: '300px' });
      if (loadMoreRef.current) observer.observe(loadMoreRef.current);
      return () => observer.disconnect();
  }, [report, visibleCount]);

  async function stepEnv() {
    if (question.length > 50 && !question.trim().startsWith("{")) {
       const resp = await fetch(`${API_BASE_URL}/analyze`, {
         method: "POST",
         headers: { "Content-Type": "application/json" },
         body: JSON.stringify({ document: question }),
       });
       if (!resp.ok) throw new Error(await resp.text());
       const data = await resp.json();
       setReport({ filename: "Input Text", ...data });
       setVisibleCount(5);
       return;
    }
    // Minimal fallback for simple text
    const resp = await fetch(`${API_BASE_URL}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document: question }),
    });
    if (!resp.ok) throw new Error(await resp.text());
    const data = await resp.json();
    setReport({ filename: "Quick Scan", ...data });
  }

  async function onFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setLastError(null);
    setBusy(true);
    setReport(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const resp = await fetch(`${API_BASE_URL}/analyze-document`, {
        method: "POST",
        body: formData,
      });
      if (!resp.ok) throw new Error(await resp.text());
      const data = (await resp.json()) as DocumentReport;
      setReport(data);
      setVisibleCount(5);
    } catch (e: any) {
      setLastError(typeof e?.message === "string" ? e.message : "Upload failed");
    } finally {
      setBusy(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  async function onSubmit() {
    setLastError(null);
    setBusy(true);
    try {
      await stepEnv();
    } catch (e: any) {
      setLastError(typeof e?.message === "string" ? e.message : "Request failed");
    } finally {
      setBusy(false);
    }
  }

  const handleExport = () => {
      window.print();
  };

  useEffect(() => {
    if (report && resultsRef.current) {
        resultsRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [report]);

  return (
    <div className="relative min-h-screen overflow-x-hidden bg-white text-ink">
      <VideoBackground />
      
      {/* Print-only Watermark */}
      <div className="hidden print:block fixed inset-0 z-0 pointer-events-none opacity-[0.03] rotate-[-45deg] flex flex-wrap gap-20 items-center justify-center text-[120px] font-bold text-black overflow-hidden select-none">
          {Array(20).fill("LEGAL ENV").map((t, i) => <span key={i}>{t}</span>)}
      </div>

      <div className="relative z-10 min-h-screen">
        <div className="h-[60px]" />

        <main className="px-6 md:px-[60px] lg:px-[120px]">
          <div className="-mt-[50px] flex flex-col items-center">
            
            {/* Header Badge */}
            <div className="animate-fade-in flex items-center gap-3 rounded-full bg-white/95 px-3 py-2 shadow-soft border border-black/5">
              <div className="flex items-center gap-2 rounded-full bg-badgeDark px-3 py-1 text-white shadow-lg">
                <StarIcon className="h-4 w-4" />
                <span className="font-inter text-[14px] font-bold">PRO</span>
              </div>
              <span className="font-inter text-[14px] font-semibold text-ink">
                AI Legal Intelligence Engine v2.0
              </span>
            </div>

            <div className="h-[34px]" />

            <h1 className="animate-slide-up text-center font-fustat text-[60px] md:text-[80px] font-extrabold leading-[0.9] tracking-[-4.8px] text-ink max-w-[900px]">
              Review Contracts at <span className="text-blue-600">AI Speed.</span>
            </h1>

            <div className="h-[44px]" />

            {/* Input Section */}
            <section className="w-full max-w-[800px] animate-fade-in-delayed">
              <div
                className="rounded-[24px] p-1 shadow-2xl overflow-hidden transform-gpu"
                style={{ background: "rgba(0,0,0,0.15)", backdropFilter: "blur(12px)" }}
              >
                <div className="rounded-[22px] bg-white p-5 shadow-inner">
                  <div className="flex flex-col gap-4">
                    <textarea
                      value={question}
                      onChange={(e) => {
                        const next = e.target.value;
                        setQuestion(next);
                        setCharCount(next.length);
                      }}
                      placeholder="Paste contract text, specific clauses, or a full legal document..."
                      className="h-[140px] w-full resize-none border-0 bg-transparent font-schibsted text-[18px] outline-none placeholder:text-black/30 leading-relaxed"
                    />

                    <div className="flex items-center justify-between pt-2 border-t border-black/5">
                        <div className="flex items-center gap-2">
                             <input type="file" ref={fileInputRef} onChange={onFileChange} className="hidden" accept=".txt" />
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                className="group flex items-center gap-2 rounded-full bg-[#f8f8f8] px-5 py-2.5 font-schibsted text-[13px] font-bold text-ink hover:bg-black hover:text-white transition-all duration-300"
                            >
                                <PaperclipIcon className="h-4 w-4 opacity-50 group-hover:opacity-100" />
                                Upload .txt
                            </button>
                            <button 
                                onClick={toggleDictation}
                                className={`hidden md:flex items-center gap-2 rounded-full px-5 py-2.5 font-schibsted text-[13px] font-bold transition-all ${isDictating ? 'bg-red-500 text-white animate-pulse shadow-lg' : 'bg-[#f8f8f8] text-ink hover:bg-[#eee]'}`}>
                                <MicrophoneIcon className={`h-4 w-4 ${isDictating ? 'opacity-100' : 'opacity-50'}`} />
                                {isDictating ? 'Listening...' : 'Dictate'}
                            </button>
                        </div>
                        <div className="flex items-center gap-4">
                             <span className="font-schibsted text-[12px] font-bold text-black/20 uppercase tracking-widest">{charCount}/10k</span>
                            <button
                                onClick={onSubmit}
                                disabled={busy || charCount < 10}
                                className="flex items-center gap-3 rounded-full bg-blue-600 px-8 py-3 font-schibsted text-[14px] font-extrabold text-white shadow-lg hover:bg-blue-700 hover:scale-105 active:scale-95 transition-all disabled:opacity-40 disabled:scale-100"
                            >
                                {busy ? "Analyzing..." : "Analyze Document"}
                                <UpArrowIcon className="h-4 w-4" />
                            </button>
                        </div>
                    </div>
                  </div>
                </div>
              </div>
              {lastError && (
                  <div className="mt-4 p-4 bg-red-50 border border-red-100 rounded-2xl text-red-600 font-schibsted text-[13px] flex items-center gap-3">
                      <div className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                      {lastError}
                  </div>
              )}
            </section>

            {/* Loading State Dashboard */}
            {busy && (
                <div className="mt-16 w-full max-w-[800px] bg-white/80 backdrop-blur-md rounded-[32px] p-12 border border-black/5 shadow-2xl flex flex-col items-center animate-fade-in">
                    <div className="h-12 w-12 border-4 border-blue-600 border-t-transparent border-l-transparent rounded-full animate-spin mb-6" />
                    <h3 className="font-fustat text-[24px] font-black tracking-tight text-ink mb-2">Analyzing Legal Risk Profile...</h3>
                    <p className="font-schibsted text-[15px] font-medium text-black/50 text-center max-w-[400px]">
                        Our AI is segmenting clauses, checking liabilities against industry standards, and generating safer rewrites.
                    </p>
                </div>
            )}

            {/* Analysis Results Dashboard */}
            {!busy && report && (
              <div id="results-dashboard" ref={resultsRef} className="mt-16 w-full max-w-[1200px] mb-32 flex flex-col lg:flex-row gap-8 animate-slide-up">
                
                {/* Left Sidebar Navigation */}
                <aside className="lg:w-[280px] shrink-0 print:hidden">
                    <div className="sticky top-10 flex flex-col gap-6">
                        <div className="rounded-[24px] bg-white/80 backdrop-blur-md p-6 shadow-soft border border-black/5 transform-gpu">
                            <h3 className="font-fustat text-[13px] font-black uppercase tracking-widest text-black/30 mb-5">Navigator</h3>
                            <div className="flex flex-col gap-2 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                                {report.results.map(r => (
                                    <button
                                        key={r.id}
                                        onClick={() => {
                                            setActiveClause(r.id);
                                            document.getElementById(`clause-${r.id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                        }}
                                        className={`flex items-center gap-3 p-3 rounded-xl transition-all ${activeClause === r.id ? 'bg-black text-white shadow-lg scale-[1.02]' : 'hover:bg-black/5'}`}
                                    >
                                        <div className={`h-2 w-2 rounded-full ${r.analysis.risk_level === 'high' ? 'bg-red-500' : r.analysis.risk_level === 'medium' ? 'bg-yellow-400' : 'bg-green-400'}`} />
                                        <span className="font-schibsted text-[14px] font-bold">Clause #{r.id}</span>
                                        <span className={`ml-auto text-[10px] font-black opacity-40 uppercase`}>{r.analysis.risk_type}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className="rounded-[24px] bg-black text-white p-6 shadow-2xl relative overflow-hidden group">
                            <div className="absolute -right-4 -top-4 h-24 w-24 bg-blue-500/20 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700" />
                            <h3 className="font-fustat text-[12px] font-black uppercase tracking-widest opacity-40 mb-1">Contract Score</h3>
                            <div className="flex items-baseline gap-2">
                                <span className="text-[48px] font-black tracking-tighter">{report.stats.score}</span>
                                <span className="text-[20px] font-black opacity-30">/100</span>
                            </div>
                            <p className="text-[11px] font-medium opacity-60 leading-relaxed mt-2">
                                Overall health index based on {report.stats.high_risk_count} critical findings.
                            </p>
                        </div>
                    </div>
                </aside>

                {/* Main Content Area */}
                <div className="flex-1 flex flex-col gap-8">
                    
                    {/* Top Stats Dashboard */}
                    <header className="rounded-[32px] bg-white/90 backdrop-blur-lg p-8 shadow-soft border border-black/5 transform-gpu">
                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-8">
                            <div className="flex-1">
                                <RiskHeatmap distribution={report.stats.distribution} />
                            </div>
                            <div className="flex gap-3 shrink-0">
                                <button
                                    onClick={handleExport}
                                    className="flex items-center gap-3 rounded-full bg-black px-8 py-4 text-[14px] font-black text-white hover:bg-black/80 shadow-2xl transition-all hover:-translate-y-1 active:translate-y-0"
                                >
                                    <DownloadIcon className="h-5 w-5" />
                                    Generate Audit
                                </button>
                            </div>
                        </div>

                        {report.stats.top_risks.length > 0 && (
                            <div className="mt-8 pt-8 border-t border-black/5 grid grid-cols-1 md:grid-cols-3 gap-6">
                                {report.stats.top_risks.map((risk: string, idx: number) => (
                                    <div key={idx} className="flex items-center gap-3 p-4 bg-red-50 rounded-2xl border border-red-100">
                                        <div className="h-8 w-8 rounded-full bg-red-500 flex items-center justify-center text-white font-bold text-[12px]">!</div>
                                        <span className="font-schibsted text-[13px] font-bold text-red-700">{risk}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </header>

                    {/* Clauses Feed */}
                    <div className="space-y-10">
                        {report.results.slice(0, visibleCount).map((res: any) => (
                            <div
                                key={res.id}
                                id={`clause-${res.id}`}
                                className={`group relative rounded-[32px] bg-white/95 border border-black/5 p-8 shadow-soft transition hover:shadow-2xl hover:-translate-y-1 duration-300 transform-gpu`}
                            >
                                {/* Header */}
                                <div className="flex items-center justify-between mb-8">
                                    <div className="flex items-center gap-4">
                                        <div className="h-10 w-10 rounded-xl bg-black flex items-center justify-center text-white font-black">
                                            {res.id}
                                        </div>
                                        <div>
                                            <div className="flex items-center gap-2">
                                                <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${
                                                    res.analysis.risk_level === 'high' ? 'bg-red-500 text-white' : 'bg-black text-white'
                                                }`}>
                                                    {res.analysis.risk_level} Risk
                                                </span>
                                                <span className="text-[12px] font-black text-black/40 uppercase tracking-widest">{res.analysis.risk_type}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <div className="flex flex-col items-end">
                                            <span className="text-[10px] font-black text-black/30 uppercase tracking-widest">Confidence</span>
                                            <div className="flex items-center gap-3 mt-1">
                                                <div className="h-1.5 w-24 bg-black/5 rounded-full overflow-hidden shadow-inner">
                                                    <div className="h-full bg-blue-500 rounded-full" style={{ width: `${res.analysis.confidence}%` }} />
                                                </div>
                                                <span className="text-[13px] font-black">{res.analysis.confidence}%</span>
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                {/* Side-by-Side Comparison */}
                                <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 mb-8">
                                    {/* Original Column */}
                                    <div className="p-6 rounded-2xl bg-[#fcfcfc] border border-black/[0.03] shadow-inner relative overflow-hidden">
                                        <div className="absolute top-0 right-0 px-3 py-1 bg-black/5 text-[9px] font-black uppercase tracking-widest text-black/30 rounded-bl-lg">Original</div>
                                        <div className="font-schibsted text-[16px] leading-relaxed text-ink/80 pt-2">
                                            <HighlightedText 
                                                text={res.clause} 
                                                red={res.analysis.highlights_red} 
                                                yellow={res.analysis.highlights_yellow} 
                                                phrases={res.analysis.phrases}
                                            />
                                        </div>
                                    </div>

                                    {/* AI Rewrite Column */}
                                    <div className="p-6 rounded-2xl bg-blue-50/50 border border-blue-100/50 shadow-soft relative transition-colors group-hover:bg-blue-50 duration-500">
                                        <div className="absolute top-0 right-0 px-3 py-1 bg-blue-600 text-[9px] font-black uppercase tracking-widest text-white rounded-bl-lg">AI SUGGESTED SAFER VERSION</div>
                                        <p className="font-schibsted text-[16px] leading-relaxed italic text-blue-900 font-medium pt-2">
                                            "{res.analysis.rewrite}"
                                        </p>
                                        <button 
                                            onClick={() => {
                                                navigator.clipboard.writeText(res.analysis.rewrite);
                                            }}
                                            className="mt-4 flex items-center gap-2 text-[12px] font-black text-blue-600 hover:text-blue-800 transition-colors"
                                        >
                                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" /></svg>
                                            COPY REWRITE
                                        </button>
                                    </div>
                                </div>

                                {/* Deep Insights Expansion */}
                                <details className="group/details border-t border-black/5 pt-6">
                                    <summary className="list-none cursor-pointer flex items-center justify-between text-[13px] font-black uppercase tracking-[0.2em] text-black/40 hover:text-black transition-colors">
                                        <span>Show Deep AI Insights</span>
                                        <span className="transition-transform group-open/details:rotate-180">↓</span>
                                    </summary>
                                    <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-8 animate-fade-in">
                                         <div className="space-y-3">
                                            <h4 className="text-[11px] font-black text-red-500 uppercase tracking-widest">Explanation</h4>
                                            <p className="text-[14px] text-mid leading-relaxed font-medium">{res.analysis.explanation}</p>
                                        </div>
                                        <div className="space-y-3">
                                            <h4 className="text-[11px] font-black text-blue-600 uppercase tracking-widest">Business Impact</h4>
                                            <p className="text-[14px] text-mid leading-relaxed font-medium">{res.analysis.impact}</p>
                                        </div>
                                    </div>
                                </details>
                            </div>
                        ))}
                        {visibleCount < report.results.length && (
                             <div ref={loadMoreRef} className="h-20 w-full flex items-center justify-center">
                                 <div className="h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin opacity-50" />
                             </div>
                        )}
                    </div>
                </div>
              </div>
            )}

          </div>
        </main>
      </div>

      <style>{`
        @keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
        @keyframes slide-up { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
        .animate-fade-in { animation: fade-in 1s ease-out forwards; }
        .animate-fade-in-delayed { animation: fade-in 1s 0.3s ease-out both; }
        .animate-slide-up { animation: slide-up 1s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
        
        .custom-scrollbar::-webkit-scrollbar { width: 4px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 10px; }

        @media print {
            .VideoBackground, .print\\:hidden, aside, button, textarea, section, details summary span:last-child {
                display: none !important;
            }
            body, .relative, main {
                background: white !important;
                color: black !important;
                padding: 0 !important;
                margin: 0 !important;
                overflow: visible !important;
            }
            main {
                max-width: 100% !important;
                width: 100% !important;
            }
            .rounded-[32px], .rounded-[24px] {
                border-radius: 8px !important;
                border: 1px solid #eee !important;
                box-shadow: none !important;
                break-inside: avoid;
            }
            details {
                display: block !important;
            }
            details[open] summary ~ * {
                display: block !important;
            }
            header {
                margin-top: 0 !important;
            }
            .h-[60px], .h-[34px], .h-[44px] {
                display: none !important;
            }
        }
      `}</style>
    </div>
  );
}

