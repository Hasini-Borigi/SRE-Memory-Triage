import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Sparkles, 
  CheckCircle2, 
  Clock, 
  ThumbsUp, 
  ThumbsDown, 
  ExternalLink, 
  CheckSquare, 
  Square,
  BookOpen,
  History,
  Layers,
  FileText,
  Lightbulb,
  ArrowRight,
  ShieldAlert,
  Loader2
} from 'lucide-react';
import { analyzeIncident, submitFeedback } from '../api';

export default function LiveIncidentView({ 
  incidents, 
  selectedIncidentId, 
  onSelectIncident, 
  onOpenResolve,
  refreshIncidents 
}) {
  const [incident, setIncident] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);
  const [completedSteps, setCompletedSteps] = useState({});
  const [feedbackSent, setFeedbackSent] = useState(false);
  const [feedbackNotes, setFeedbackNotes] = useState('');
  const [submittingFeedback, setSubmittingFeedback] = useState(false);

  // Sync selected incident
  useEffect(() => {
    if (!incidents || incidents.length === 0) return;
    const current = incidents.find(i => i.id === selectedIncidentId) || incidents[0];
    setIncident(current);
    setAnalysis(null);
    setCompletedSteps({});
    setFeedbackSent(false);
    setFeedbackNotes('');
    setError(null);
  }, [selectedIncidentId, incidents]);

  const handleAnalyze = async () => {
    if (!incident) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const result = await analyzeIncident(incident.id);
      setAnalysis(result);
      if (refreshIncidents) refreshIncidents();
    } catch (err) {
      setError(err.message || 'Failed to analyze incident');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const toggleStep = (index) => {
    setCompletedSteps(prev => ({
      ...prev,
      [index]: !prev[index]
    }));
  };

  const handleFeedback = async (helpful) => {
    if (!incident || !analysis) return;
    setSubmittingFeedback(true);
    try {
      await submitFeedback(incident.id, {
        runbook_id: analysis.recommended_runbook?.id || null,
        helpful,
        notes: feedbackNotes,
      });
      setFeedbackSent(true);
      if (refreshIncidents) refreshIncidents();
    } catch (err) {
      setError('Failed to record feedback');
    } finally {
      setSubmittingFeedback(false);
    }
  };

  if (!incident) {
    return (
      <div className="py-20 text-center">
        <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mx-auto mb-3" />
        <p className="text-slate-400 text-sm">Loading incident telemetry...</p>
      </div>
    );
  }

  const isResolved = incident.status === 'RESOLVED';
  const sevColor = 
    incident.severity === 'SEV1' ? 'bg-red-500/10 text-red-400 border-red-500/30' :
    incident.severity === 'SEV2' ? 'bg-amber-500/10 text-amber-400 border-amber-500/30' :
    'bg-blue-500/10 text-blue-400 border-blue-500/30';

  const statusColor = 
    incident.status === 'RESOLVED' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' :
    incident.status === 'INVESTIGATING' ? 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30' :
    'bg-rose-500/10 text-rose-400 border-rose-500/30 animate-pulse';

  return (
    <div className="space-y-6">
      {/* Top Banner & Incident Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 glass-panel p-4 rounded-xl">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              Active Triage Workspace
              <span className={`text-[11px] font-semibold uppercase px-2.5 py-0.5 rounded-full border ${statusColor}`}>
                {incident.status}
              </span>
            </h2>
            <p className="text-xs text-slate-400">Select an incident to triage or analyze memory suggestions</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-xs text-slate-400 font-medium">Incident:</label>
          <select
            value={incident.id}
            onChange={(e) => onSelectIncident(e.target.value)}
            className="bg-slate-900 border border-slate-700 text-xs text-white rounded-lg px-3 py-2 outline-none focus:border-indigo-500 font-mono"
          >
            {incidents.map((inc) => (
              <option key={inc.id} value={inc.id}>
                [{inc.id}] {inc.title.length > 50 ? inc.title.slice(0, 50) + '...' : inc.title}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Incident Details Card */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <span className="font-mono text-xs font-bold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                {incident.id}
              </span>
              <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${sevColor}`}>
                {incident.severity}
              </span>
              <span className="text-xs font-mono text-slate-400 bg-slate-800/80 px-2.5 py-0.5 rounded">
                service: {incident.service}
              </span>
              {incident.category && (
                <span className="text-xs text-slate-400 bg-slate-800/40 px-2 py-0.5 rounded border border-slate-700">
                  {incident.category}
                </span>
              )}
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight">{incident.title}</h1>
          </div>

          <div className="flex items-center gap-3">
            {!isResolved ? (
              <button
                onClick={() => onOpenResolve(incident)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-xs font-medium transition cursor-pointer"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Resolve Incident</span>
              </button>
            ) : (
              <div className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-lg border border-emerald-500/20">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Resolved ({incident.time_to_resolve_min}m MTTR)</span>
              </div>
            )}
          </div>
        </div>

        {/* Symptoms & Telemetry */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 space-y-1.5">
            <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              Observed Symptoms
            </span>
            <p className="text-sm text-slate-200 leading-relaxed">{incident.symptoms}</p>
          </div>

          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800/80 space-y-1.5">
            <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-cyan-400" />
              Logs Snippet
            </span>
            <pre className="code-font text-xs text-rose-300/90 bg-black/40 p-2.5 rounded-lg overflow-x-auto whitespace-pre-wrap leading-tight border border-rose-950/40">
              {incident.logs_snippet || 'No logs attached to telemetry.'}
            </pre>
          </div>
        </div>

        {/* Timeline Preview */}
        {incident.timeline && incident.timeline.length > 0 && (
          <div className="border-t border-slate-800/80 pt-4 space-y-2">
            <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold flex items-center gap-1.5">
              <History className="w-3.5 h-3.5 text-indigo-400" />
              Incident Timeline
            </span>
            <div className="space-y-1.5">
              {incident.timeline.map((event, idx) => (
                <div key={idx} className="flex items-center gap-3 text-xs text-slate-300">
                  <span className="font-mono text-slate-500 text-[11px] w-24 truncate">
                    {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : 'Recent'}
                  </span>
                  <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />
                  <span>{event.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Analyze Action Bar */}
        <div className="border-t border-slate-800 pt-4 flex items-center justify-between">
          <div className="text-xs text-slate-400">
            {analysis 
              ? 'Memory triage complete. Inspect root cause hypothesis and resolution runbook below.' 
              : 'Trigger autonomous memory recall to discover matching past outages and runbooks.'}
          </div>

          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 via-indigo-600 to-cyan-500 hover:from-indigo-600 hover:to-cyan-600 text-white font-semibold text-xs shadow-lg shadow-indigo-500/25 transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Recalling Hindsight Memory...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-cyan-200" />
                <span>Analyze Incident with Memory</span>
              </>
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-xs">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Analysis Results View */}
      {analysis && (
        <div className="space-y-6 animate-fadeIn">
          {/* Section: Probable Root Cause & Rationale */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-indigo-900/40 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-indigo-400 font-bold text-sm">
                  <Lightbulb className="w-4 h-4 text-amber-400" />
                  <span>Probable Root Cause Hypothesis</span>
                </div>

                <div className="flex items-center gap-2 bg-slate-900 px-3 py-1 rounded-full border border-slate-800">
                  <span className="text-[11px] text-slate-400">Confidence:</span>
                  <span className="text-xs font-bold text-emerald-400 font-mono">
                    {Math.round(analysis.confidence * 100)}%
                  </span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-800/40 text-sm text-slate-100 font-medium leading-relaxed">
                {analysis.probable_root_cause}
              </div>

              {/* Why Explanation & Explicit Historical Citations */}
              <div className="space-y-1.5">
                <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold">
                  Why this conclusion (Memory Rationale & Citations):
                </span>
                <p className="text-xs text-slate-300 leading-relaxed bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
                  {analysis.why_explanation}
                </p>
                {analysis.cited_incident_ids && analysis.cited_incident_ids.length > 0 && (
                  <div className="flex items-center gap-2 pt-1 text-xs">
                    <span className="text-slate-400 font-medium">Historical Citations:</span>
                    {analysis.cited_incident_ids.map(id => (
                      <span key={id} className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 font-mono text-[11px]">
                        {id}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Recommended Runbook Card */}
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                    Recommended Runbook
                  </span>
                  {analysis.recommended_runbook && (
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                      {Math.round(analysis.recommended_runbook.success_rate * 100)}% Success Rate
                    </span>
                  )}
                </div>

                {analysis.recommended_runbook ? (
                  <div className="space-y-2">
                    <div className="font-mono text-xs font-bold text-cyan-400">
                      {analysis.recommended_runbook.id}: {analysis.recommended_runbook.title}
                    </div>
                    <p className="text-xs text-slate-400 line-clamp-3">
                      {analysis.recommended_runbook.description}
                    </p>
                    <div className="grid grid-cols-2 gap-2 pt-2 text-[11px] text-slate-300">
                      <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                        <span className="text-slate-500 block text-[10px]">Usage Count</span>
                        <span className="font-bold text-white font-mono">{analysis.recommended_runbook.times_worked} / {analysis.recommended_runbook.times_suggested} worked</span>
                      </div>
                      <div className="bg-slate-900/80 p-2 rounded-lg border border-slate-800">
                        <span className="text-slate-500 block text-[10px]">Avg MTTR</span>
                        <span className="font-bold text-emerald-400 font-mono">{analysis.recommended_runbook.avg_mttr_min}m</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="py-6 text-center text-xs text-slate-400">
                    No exact runbook matched. Follow ranked resolution checklist below.
                  </div>
                )}
              </div>

              {/* Feedback Trigger */}
              <div className="border-t border-slate-800 pt-3 space-y-2">
                <span className="text-[10px] text-slate-400 block font-medium">Was this suggestion helpful?</span>
                {feedbackSent ? (
                  <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>Feedback retained in memory!</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleFeedback(true)}
                      disabled={submittingFeedback}
                      className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 text-xs font-medium transition cursor-pointer"
                    >
                      <ThumbsUp className="w-3.5 h-3.5 text-emerald-400" />
                      <span>Helpful</span>
                    </button>
                    <button
                      onClick={() => handleFeedback(false)}
                      disabled={submittingFeedback}
                      className="flex-1 inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-200 border border-slate-700 text-xs font-medium transition cursor-pointer"
                    >
                      <ThumbsDown className="w-3.5 h-3.5 text-rose-400" />
                      <span>Not Helpful</span>
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Section: Ranked Resolution Steps Checklist */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckSquare className="w-4 h-4 text-cyan-400" />
                <h3 className="font-bold text-white text-sm">Ranked Actionable Resolution Checklist</h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                {Object.values(completedSteps).filter(Boolean).length} of {analysis.ranked_resolution_steps.length} verified
              </span>
            </div>

            <div className="space-y-2">
              {analysis.ranked_resolution_steps.map((step, idx) => {
                const isDone = completedSteps[idx];
                return (
                  <div
                    key={idx}
                    onClick={() => toggleStep(idx)}
                    className={`flex items-start gap-3 p-3 rounded-xl border transition cursor-pointer ${
                      isDone 
                        ? 'bg-emerald-950/20 border-emerald-800/40 text-slate-400 line-through' 
                        : 'bg-slate-900/60 border-slate-800 hover:border-slate-700 text-slate-200'
                    }`}
                  >
                    <div className="mt-0.5">
                      {isDone ? (
                        <CheckSquare className="w-4 h-4 text-emerald-400" />
                      ) : (
                        <Square className="w-4 h-4 text-slate-500" />
                      )}
                    </div>
                    <span className="text-xs leading-relaxed flex-1">
                      <strong className="text-slate-400 font-mono mr-1.5">Step {idx + 1}:</strong>
                      {step}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Section: Similar Historical Incidents with Explainable Score Breakdown */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Layers className="w-4 h-4 text-indigo-400" />
                <h3 className="font-bold text-white text-sm">Similar Historical Incidents (Hybrid Memory Retrieval)</h3>
              </div>
              <span className="text-xs text-slate-400">
                Formula: 0.40·Sim + 0.20·Service + 0.15·Sev + 0.15·Runbook + 0.10·Recency
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {analysis.similar_incidents.map((match) => {
                const b = match.score_breakdown;
                return (
                  <div key={match.incident_id} className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-500/10 px-2 py-0.5 rounded border border-cyan-500/20">
                          {match.incident_id}
                        </span>
                        <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                          {match.service}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-[11px] text-slate-400 font-medium">Match Score:</span>
                        <span className="text-xs font-bold text-indigo-400 font-mono">
                          {Math.round(match.score * 100)}%
                        </span>
                      </div>
                    </div>

                    <h4 className="text-xs font-semibold text-slate-200 line-clamp-2">{match.title}</h4>

                    <div className="text-[11px] text-slate-400 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                      <span className="text-slate-500 font-semibold block text-[10px] uppercase">Prior Root Cause:</span>
                      {match.root_cause || 'Underlying hardware/software fault'}
                    </div>

                    {/* Explainable Score Breakdown */}
                    <div className="border-t border-slate-800/60 pt-2.5 space-y-1">
                      <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider block">
                        Explainable Score Weights:
                      </span>
                      <div className="grid grid-cols-5 gap-1 text-[10px] text-center font-mono">
                        <div className="bg-slate-950 p-1 rounded border border-slate-800">
                          <span className="text-slate-500 block">Vector</span>
                          <span className="text-cyan-400 font-bold">{b?.vector_similarity ?? 0.85}</span>
                        </div>
                        <div className="bg-slate-950 p-1 rounded border border-slate-800">
                          <span className="text-slate-500 block">Service</span>
                          <span className="text-cyan-400 font-bold">{b?.service_match ?? 1.0}</span>
                        </div>
                        <div className="bg-slate-950 p-1 rounded border border-slate-800">
                          <span className="text-slate-500 block">Severity</span>
                          <span className="text-cyan-400 font-bold">{b?.severity_match ?? 1.0}</span>
                        </div>
                        <div className="bg-slate-950 p-1 rounded border border-slate-800">
                          <span className="text-slate-500 block">Runbook</span>
                          <span className="text-cyan-400 font-bold">{b?.runbook_success_rate ?? 0.9}</span>
                        </div>
                        <div className="bg-slate-950 p-1 rounded border border-slate-800">
                          <span className="text-slate-500 block">Recency</span>
                          <span className="text-cyan-400 font-bold">{b?.recency_factor ?? 0.8}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Section: Post-Mortem Lessons Learned */}
          {analysis.post_mortem_lessons && analysis.post_mortem_lessons.length > 0 && (
            <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-3">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-emerald-400" />
                <h3 className="font-bold text-white text-sm">Recalled Post-Mortem Preventive Rules</h3>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {analysis.post_mortem_lessons.map((lesson, idx) => (
                  <div key={idx} className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mt-1.5 shrink-0" />
                    <span>{lesson}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
