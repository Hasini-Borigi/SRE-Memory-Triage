import React, { useState } from 'react';
import { X, ShieldAlert, AlertTriangle, FileText, Loader2 } from 'lucide-react';
import { createIncident } from '../api';

export default function CreateIncidentModal({ isOpen, onClose, onCreated }) {
  const [title, setTitle] = useState('');
  const [service, setService] = useState('payment-service');
  const [severity, setSeverity] = useState('SEV1');
  const [symptoms, setSymptoms] = useState('');
  const [logsSnippet, setLogsSnippet] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title || !symptoms) {
      setError('Title and symptoms are required.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const newInc = await createIncident({
        title,
        service,
        severity,
        symptoms,
        logs_snippet: logsSnippet,
      });
      onCreated(newInc);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create incident');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDemoPreset = () => {
    setTitle('DB connection timeouts after checkout deploy on payment-service');
    setService('postgres-primary');
    setSeverity('SEV1');
    setSymptoms('Elevated 504 Gateway Timeouts on payment checkout. Latency spiked to 8500ms and active database connection pool exhausted.');
    setLogsSnippet('psycopg2.OperationalError: FATAL: remaining connection slots are reserved for non-replication superuser connections\nat /app/db.py:42 in get_db_connection()');
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Report Production Outage</h3>
              <p className="text-xs text-slate-400">Dispatch live incident to memory agent triage</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Demo Preset Button */}
        <div className="px-5 pt-1">
          <button
            type="button"
            onClick={handleDemoPreset}
            className="w-full py-1.5 px-3 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 text-xs font-medium transition cursor-pointer flex items-center justify-center gap-1.5"
          >
            <span>⚡ Load Demo Scenario Preset: "DB connection timeouts after deploy"</span>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-5 pb-5 space-y-4 text-xs">
          {error && (
            <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label className="text-slate-300 font-medium">Incident Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Elevated 504 Gateway Timeouts in payment-service"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-indigo-500 text-xs"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-slate-300 font-medium">Affected Service *</label>
              <select
                value={service}
                onChange={(e) => setService(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-indigo-500 text-xs font-mono"
              >
                <option value="postgres-primary">postgres-primary</option>
                <option value="payment-service">payment-service</option>
                <option value="api-gateway">api-gateway</option>
                <option value="redis-cluster">redis-cluster</option>
                <option value="k8s-ingress">k8s-ingress</option>
                <option value="kafka-pipeline">kafka-pipeline</option>
                <option value="auth-service">auth-service</option>
              </select>
            </div>

            <div className="space-y-1">
              <label className="text-slate-300 font-medium">Severity Tier *</label>
              <select
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-indigo-500 text-xs font-mono"
              >
                <option value="SEV1">SEV1 - Critical Outage</option>
                <option value="SEV2">SEV2 - Major Degradation</option>
                <option value="SEV3">SEV3 - Minor Issue</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-slate-300 font-medium">Observed Symptoms *</label>
            <textarea
              rows={3}
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              placeholder="Describe error rates, impacted endpoints, customer impact..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:border-indigo-500 text-xs"
            />
          </div>

          <div className="space-y-1">
            <label className="text-slate-300 font-medium">Logs Snippet (Optional)</label>
            <textarea
              rows={2}
              value={logsSnippet}
              onChange={(e) => setLogsSnippet(e.target.value)}
              placeholder="Paste stack trace or server log excerpt..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:border-indigo-500 text-xs font-mono"
            />
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
              className="px-5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium transition text-xs flex items-center gap-1.5 disabled:opacity-50"
            >
              {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>Submit Incident</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
