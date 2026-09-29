import React, { useState } from 'react';
import { 
  Search, 
  Database, 
  Layers, 
  Sparkles, 
  FileText, 
  BookOpen, 
  ShieldAlert, 
  PlusCircle,
  ExternalLink,
  Loader2
} from 'lucide-react';
import { searchMemory } from '../api';

export default function MemoryExplorerView({ onOpenPostMortem }) {
  const [query, setQuery] = useState('Postgres connection pool exhaustion');
  const [filterType, setFilterType] = useState('all');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await searchMemory(query, filterType);
      setResults(data);
      setSearched(true);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const sampleQueries = [
    'Postgres connection pool timeouts',
    'Redis memory leak OOM allkeys-lru',
    'Expired SSL certificate ingress handshake',
    'Kafka consumer group partition rebalance',
    'CoreDNS lookup timeout across pods',
  ];

  return (
    <div className="space-y-6">
      {/* Search Header Banner */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Database className="w-5 h-5 text-indigo-400" />
              Persistent Memory Bank Inspector (Vectorize Hindsight)
            </h2>
            <p className="text-xs text-slate-400">
              Query episodic incidents, semantic runbooks, and post-mortems stored in memory
            </p>
          </div>

          <button
            onClick={onOpenPostMortem}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 text-xs font-medium transition cursor-pointer"
          >
            <PlusCircle className="w-4 h-4" />
            <span>Ingest Post-Mortem</span>
          </button>
        </div>

        {/* Search Input Box */}
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search persistent memory for failure patterns, stack traces, or runbooks..."
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-slate-500 outline-none focus:border-indigo-500 font-mono"
            />
          </div>

          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white outline-none focus:border-indigo-500 font-mono"
          >
            <option value="all">All Memory Types</option>
            <option value="incident">Incidents (Episodic)</option>
            <option value="runbook">Runbooks (Semantic)</option>
            <option value="postmortem">Post-Mortems (Lessons)</option>
          </select>

          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-lg shadow-indigo-500/20 transition cursor-pointer disabled:opacity-50"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            <span>Recall</span>
          </button>
        </form>

        {/* Quick Sample Queries */}
        <div className="flex flex-wrap items-center gap-2 pt-1 text-xs">
          <span className="text-[11px] text-slate-500 font-medium">Try query:</span>
          {sampleQueries.map((q) => (
            <button
              key={q}
              onClick={() => {
                setQuery(q);
              }}
              className="px-2.5 py-1 rounded-lg bg-slate-900/80 hover:bg-slate-800 border border-slate-800 text-[11px] text-slate-300 transition cursor-pointer font-mono"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Memory Results */}
      <div className="space-y-3.5">
        <div className="flex items-center justify-between text-xs text-slate-400 px-1">
          <span>{searched ? `Found ${results.length} memory units` : 'Perform a recall query above'}</span>
          <span className="font-mono text-slate-500 text-[11px]">Backend: Hindsight (Cloud Graph & Vectors)</span>
        </div>

        {results.map((res) => {
          const typeIcon = 
            res.type === 'incident' ? ShieldAlert :
            res.type === 'runbook' ? BookOpen :
            FileText;

          const typeBadgeColor = 
            res.type === 'incident' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
            res.type === 'runbook' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' :
            'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';

          const Icon = typeIcon;

          return (
            <div
              key={res.id}
              className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3"
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full border flex items-center gap-1 ${typeBadgeColor}`}>
                    <Icon className="w-3 h-3" />
                    {res.type}
                  </span>
                  <span className="font-mono text-xs font-bold text-white">
                    {res.id}
                  </span>
                  {res.metadata?.service && (
                    <span className="text-[11px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      {res.metadata.service}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1.5 text-xs">
                  <span className="text-slate-400 text-[11px]">Similarity:</span>
                  <span className="font-mono font-bold text-indigo-400">
                    {Math.round(res.score * 100)}%
                  </span>
                </div>
              </div>

              <h4 className="text-sm font-bold text-white">{res.title}</h4>

              <pre className="text-xs text-slate-300 bg-slate-950/70 p-3 rounded-xl border border-slate-800/80 whitespace-pre-wrap font-sans leading-relaxed">
                {res.content}
              </pre>

              {res.metadata && Object.keys(res.metadata).length > 0 && (
                <div className="flex flex-wrap gap-2 pt-1 border-t border-slate-800/60 text-[10px] font-mono text-slate-500">
                  {Object.entries(res.metadata).map(([k, v]) => (
                    <span key={k} className="bg-slate-900 px-2 py-0.5 rounded">
                      {k}: {String(v)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {searched && results.length === 0 && (
          <div className="py-16 text-center glass-panel rounded-2xl border border-slate-800 text-slate-400 text-xs">
            No memories matched your query. Try broader keywords or inspect available runbooks.
          </div>
        )}
      </div>
    </div>
  );
}
