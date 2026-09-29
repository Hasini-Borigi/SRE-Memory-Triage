import React from 'react';
import { 
  ShieldAlert, 
  Activity, 
  Database, 
  Cpu, 
  BookOpen, 
  Search, 
  BarChart3, 
  PlusCircle,
  Key
} from 'lucide-react';

export default function Header({ 
  activeTab, 
  setActiveTab, 
  health, 
  onOpenCreate 
}) {
  const isGroqActive = health?.llm_provider === 'groq';
  const isHindsightActive = health?.memory_backend === 'hindsight';

  return (
    <header className="border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => setActiveTab('live')}>
            <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 text-white shadow-lg shadow-indigo-500/25">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-white tracking-tight">SRE Memory Triage</span>
                <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                  Agent v1.0
                </span>
              </div>
              <p className="text-xs text-slate-400">Autonomous Incident Response with Persistent Memory</p>
            </div>
          </div>

          {/* Component Badges */}
          <div className="hidden lg:flex items-center gap-3">
            {/* LLM Status Badge */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
              <Cpu className="w-3.5 h-3.5 text-cyan-400" />
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5">
                  <span className="font-medium text-slate-300">LLM:</span>
                  <span className="font-bold uppercase tracking-wider text-cyan-400">
                    {health?.llm_provider || 'Groq'}
                  </span>
                  <span className={`w-2 h-2 rounded-full ${isGroqActive ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'}`} />
                </div>
                <span className="text-[10px] text-slate-500 font-mono">
                  {health?.llm_model || 'llama-3.3-70b-versatile'}
                </span>
              </div>
            </div>

            {/* Memory Backend Badge */}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
              <Database className="w-3.5 h-3.5 text-indigo-400" />
              <div className="flex flex-col">
                <div className="flex items-center gap-1.5">
                  <span className="font-medium text-slate-300">Memory:</span>
                  <span className="font-bold uppercase tracking-wider text-indigo-400">
                    {health?.memory_backend || 'Hindsight'}
                  </span>
                  <span className={`w-2 h-2 rounded-full ${isHindsightActive ? 'bg-emerald-400 animate-pulse' : 'bg-cyan-400'}`} />
                </div>
                <span className="text-[10px] text-slate-500 font-mono">
                  {isHindsightActive ? 'Vectorize Graph+Episodic' : 'ChromaDB Local'}
                </span>
              </div>
            </div>

            {/* Masked Key Pill */}
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-900/60 border border-slate-800/80 text-[11px] text-slate-400 font-mono">
              <Key className="w-3 h-3 text-slate-500" />
              <span>{health?.groq_key_masked || 'gsk_****'}</span>
              <span className="text-slate-600">|</span>
              <span>{health?.hindsight_key_masked || 'hsk_****'}</span>
            </div>
          </div>

          {/* Action Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={onOpenCreate}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-gradient-to-r from-indigo-500 to-cyan-500 hover:from-indigo-600 hover:to-cyan-600 text-white font-medium text-xs shadow-lg shadow-indigo-500/20 transition-all active:scale-95 cursor-pointer"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Report Incident</span>
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav className="flex space-x-1 border-t border-slate-800/60 pt-1 -mb-px">
          {[
            { id: 'live', label: 'Live Triage', icon: Activity },
            { id: 'history', label: 'Incident History', icon: ShieldAlert },
            { id: 'runbooks', label: 'Runbook Library', icon: BookOpen },
            { id: 'memory', label: 'Memory Explorer', icon: Search },
            { id: 'analytics', label: 'Analytics & MTTR', icon: BarChart3 },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs font-medium border-b-2 transition-all cursor-pointer ${
                  isActive
                    ? 'border-indigo-500 text-indigo-400 bg-indigo-500/5'
                    : 'border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-indigo-400' : 'text-slate-500'}`} />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
