import React, { useState } from 'react';
import { 
  ShieldAlert, 
  Search, 
  Filter, 
  Clock, 
  CheckCircle2, 
  ArrowRight,
  Database,
  Calendar
} from 'lucide-react';

export default function IncidentHistoryView({ incidents, onSelectIncident }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedService, setSelectedService] = useState('ALL');
  const [selectedSeverity, setSelectedSeverity] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');

  const services = ['ALL', ...new Set(incidents.map(i => i.service))];
  const severities = ['ALL', 'SEV1', 'SEV2', 'SEV3'];
  const statuses = ['ALL', 'OPEN', 'INVESTIGATING', 'RESOLVED'];

  const filteredIncidents = incidents.filter(inc => {
    const matchesSearch = 
      inc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      inc.symptoms.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (inc.root_cause && inc.root_cause.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesService = selectedService === 'ALL' || inc.service === selectedService;
    const matchesSeverity = selectedSeverity === 'ALL' || inc.severity === selectedSeverity;
    const matchesStatus = selectedStatus === 'ALL' || inc.status === selectedStatus;

    return matchesSearch && matchesService && matchesSeverity && matchesStatus;
  });

  return (
    <div className="space-y-6">
      {/* Search & Filters Bar */}
      <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="relative w-full md:w-96">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by title, symptoms, or root cause..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-900/90 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex flex-wrap items-center gap-3 w-full md:w-auto">
            {/* Service Filter */}
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <Filter className="w-3.5 h-3.5 text-slate-500" />
              <span>Service:</span>
              <select
                value={selectedService}
                onChange={(e) => setSelectedService(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white font-mono"
              >
                {services.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            {/* Severity Filter */}
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <span>Severity:</span>
              <select
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white font-mono"
              >
                {severities.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-1.5 text-xs text-slate-400">
              <span>Status:</span>
              <select
                value={selectedStatus}
                onChange={(e) => setSelectedStatus(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-xs text-white font-mono"
              >
                {statuses.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800/80">
          <span>Showing {filteredIncidents.length} of {incidents.length} incidents</span>
          <span>Filtered from episodic memory repository</span>
        </div>
      </div>

      {/* Incident List */}
      <div className="grid grid-cols-1 gap-3.5">
        {filteredIncidents.map((inc) => {
          const sevColor = 
            inc.severity === 'SEV1' ? 'bg-red-500/10 text-red-400 border-red-500/30' :
            inc.severity === 'SEV2' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
            'bg-blue-500/10 text-blue-400 border-blue-500/30';

          const statusColor = 
            inc.status === 'RESOLVED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
            inc.status === 'INVESTIGATING' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' :
            'bg-rose-500/10 text-rose-400 border-rose-500/30';

          return (
            <div
              key={inc.id}
              className="glass-panel glass-panel-hover p-4.5 rounded-xl border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                    {inc.id}
                  </span>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${sevColor}`}>
                    {inc.severity}
                  </span>
                  <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                    {inc.service}
                  </span>
                  <span className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${statusColor}`}>
                    {inc.status}
                  </span>
                  {inc.runbook_id && (
                    <span className="text-[10px] font-mono text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                      {inc.runbook_id}
                    </span>
                  )}
                </div>

                <h3 className="text-sm font-bold text-white">{inc.title}</h3>
                <p className="text-xs text-slate-400 line-clamp-1">{inc.symptoms}</p>

                {inc.root_cause && (
                  <div className="text-[11px] text-slate-300 bg-slate-950/40 px-2.5 py-1.5 rounded-lg border border-slate-800/60 line-clamp-1">
                    <strong className="text-slate-400 font-semibold mr-1">RCA:</strong>
                    {inc.root_cause}
                  </div>
                )}
              </div>

              {/* Action & Stats */}
              <div className="flex items-center gap-4 md:border-l md:border-slate-800 md:pl-5 shrink-0">
                <div className="text-right text-[11px] text-slate-400 space-y-0.5">
                  <div className="flex items-center gap-1 text-slate-400 justify-end">
                    <Clock className="w-3 h-3 text-slate-500" />
                    <span>{inc.time_to_resolve_min ? `${inc.time_to_resolve_min}m MTTR` : 'Active'}</span>
                  </div>
                  <div className="text-slate-500 text-[10px]">
                    {inc.created_at ? new Date(inc.created_at).toLocaleDateString() : 'Recent'}
                  </div>
                </div>

                <button
                  onClick={() => onSelectIncident(inc.id)}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 text-xs font-medium transition cursor-pointer"
                >
                  <span>Triage</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
