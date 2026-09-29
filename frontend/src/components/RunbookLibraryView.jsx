import React, { useState } from 'react';
import { 
  BookOpen, 
  Search, 
  CheckCircle2, 
  TrendingUp, 
  Clock, 
  ChevronDown, 
  ChevronUp, 
  PlusCircle,
  ShieldCheck,
  Zap
} from 'lucide-react';

export default function RunbookLibraryView({ runbooks, onOpenCreateRunbook }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedService, setSelectedService] = useState('ALL');
  const [expandedId, setExpandedId] = useState(null);

  const services = ['ALL', ...new Set(runbooks.map(r => r.service))];

  const filteredRunbooks = runbooks.filter(rb => {
    const matchesSearch = 
      rb.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rb.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      rb.id.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesService = selectedService === 'ALL' || rb.service === selectedService;
    return matchesSearch && matchesService;
  });

  const toggleExpand = (id) => {
    setExpandedId(prev => prev === id ? null : id);
  };

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 glass-panel p-5 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-cyan-400" />
            Standard Operating Runbook Catalog
          </h2>
          <p className="text-xs text-slate-400">
            Empirically ranked runbooks with feedback-weighted success metrics stored in Hindsight memory
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search runbooks..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-xl pl-9 pr-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none focus:border-cyan-500"
            />
          </div>

          <select
            value={selectedService}
            onChange={(e) => setSelectedService(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white font-mono"
          >
            {services.map(s => <option key={s} value={s}>{s}</option>)}
          </select>

          <button
            onClick={onOpenCreateRunbook}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-medium transition cursor-pointer"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Add Runbook</span>
          </button>
        </div>
      </div>

      {/* Runbook Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredRunbooks.map((rb) => {
          const isExpanded = expandedId === rb.id;
          const successPct = Math.round(rb.success_rate * 100);

          return (
            <div
              key={rb.id}
              className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                        {rb.id}
                      </span>
                      <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                        {rb.service}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-white leading-snug">{rb.title}</h3>
                  </div>

                  <span className={`text-[10px] font-bold px-2.5 py-1 rounded-full border shrink-0 ${
                    successPct >= 90 ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
                    successPct >= 75 ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' :
                    'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  }`}>
                    {successPct}% Success
                  </span>
                </div>

                <p className="text-xs text-slate-400 leading-relaxed">{rb.description}</p>

                {/* Metrics Pill Grid */}
                <div className="grid grid-cols-3 gap-2 pt-1 text-[11px]">
                  <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800 text-center">
                    <span className="text-slate-500 block text-[10px]">Suggested</span>
                    <span className="font-bold text-white font-mono">{rb.times_suggested}</span>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800 text-center">
                    <span className="text-slate-500 block text-[10px]">Worked</span>
                    <span className="font-bold text-emerald-400 font-mono">{rb.times_worked}</span>
                  </div>
                  <div className="bg-slate-900/80 p-2 rounded-xl border border-slate-800 text-center">
                    <span className="text-slate-500 block text-[10px]">Avg MTTR</span>
                    <span className="font-bold text-cyan-400 font-mono">{rb.avg_mttr_min}m</span>
                  </div>
                </div>

                {/* Steps Details */}
                {isExpanded && (
                  <div className="border-t border-slate-800 pt-3 space-y-2 animate-fadeIn">
                    <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold block">
                      Execution Procedure ({rb.steps?.length || 0} steps):
                    </span>
                    <div className="space-y-1.5">
                      {rb.steps?.map((step, idx) => (
                        <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-300 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                          <span className="font-mono text-cyan-400 font-bold shrink-0">{idx + 1}.</span>
                          <span className="leading-relaxed">{step}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Expand Toggle */}
              <button
                onClick={() => toggleExpand(rb.id)}
                className="w-full flex items-center justify-center gap-1.5 pt-2 text-xs text-slate-400 hover:text-white transition cursor-pointer border-t border-slate-800/60"
              >
                <span>{isExpanded ? 'Hide Steps' : 'View Standard Operating Steps'}</span>
                {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
