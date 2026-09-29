import React, { useState } from 'react';
import { X, CheckCircle2, Clock, BookOpen, Loader2 } from 'lucide-react';
import { resolveIncident } from '../api';

export default function ResolveModal({ isOpen, onClose, incident, onResolved }) {
  const [rootCause, setRootCause] = useState(incident?.root_cause || '');
  const [runbookId, setRunbookId] = useState(incident?.runbook_id || 'RB-001');
  const [timeToResolve, setTimeToResolve] = useState(18);
  const [outcome, setOutcome] = useState('SUCCESS');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen || !incident) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const updated = await resolveIncident(incident.id, {
        root_cause: rootCause || 'Connection pool exhaustion resolved via PgBouncer scaling',
        runbook_id: runbookId,
        time_to_resolve_min: Number(timeToResolve) || 18,
        outcome,
        resolution_steps: [
          'Terminated leaked idle database connections',
          'Increased PgBouncer connection ceiling',
          'Verified error rates returned to baseline',
        ],
      });
      onResolved(updated);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to resolve incident');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl space-y-4">
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <CheckCircle2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Resolve Incident {incident.id}</h3>
              <p className="text-xs text-slate-400">Save post-mitigation learnings into episodic memory</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-5 pb-5 space-y-4 text-xs">
          {error && (
            <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label className="text-slate-300 font-medium">Confirmed Root Cause *</label>
            <textarea
              rows={2}
              value={rootCause}
              onChange={(e) => setRootCause(e.target.value)}
              placeholder="e.g. Connection pool exhaustion due to missing checkout timeout"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:border-emerald-500 text-xs"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-slate-300 font-medium">Runbook Applied</label>
              <select
                value={runbookId}
                onChange={(e) => setRunbookId(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-emerald-500 text-xs font-mono"
              >
                <option value="RB-001">RB-001: Postgres Pool</option>
                <option value="RB-002">RB-002: Redis Eviction</option>
                <option value="RB-003">RB-003: Pod CrashLoop</option>
                <option value="RB-004">RB-004: TLS Renewal</option>
                <option value="RB-005">RB-005: Kafka Lag</option>
                <option value="RB-006">RB-006: Postgres WAL</option>
                <option value="RB-007">RB-007: CoreDNS</option>
                <option value="RB-008">RB-008: Payment Webhook</option>
                <option value="RB-009">RB-009: Auth JWKS</option>
                <option value="RB-010">RB-010: Nginx Timeout</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-slate-300 font-medium">MTTR (Minutes) *</label>
              <input
                type="number"
                min="1"
                max="600"
                value={timeToResolve}
                onChange={(e) => setTimeToResolve(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-emerald-500 text-xs font-mono"
              />
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-slate-300 font-medium">Resolution Outcome</label>
            <select
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-emerald-500 text-xs font-mono"
            >
              <option value="SUCCESS">SUCCESS - Full Recovery</option>
              <option value="MITIGATED">MITIGATED - Temporary Workaround</option>
              <option value="ESCALATED">ESCALATED - Vendor Escalation</option>
            </select>
          </div>

          <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-medium transition text-xs flex items-center gap-1.5 disabled:opacity-50"
            >
              {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>Commit Resolution</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
