import React, { useState } from 'react';
import { X, FileText, Loader2, Sparkles } from 'lucide-react';
import { createPostMortem } from '../api';

export default function PostMortemModal({ isOpen, onClose, onCreated }) {
  const [title, setTitle] = useState('');
  const [service, setService] = useState('postgres-primary');
  const [content, setContent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title || !content) {
      setError('Title and post-mortem content are required.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const pm = await createPostMortem({
        title,
        service,
        content,
      });
      if (onCreated) onCreated(pm);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to ingest post-mortem');
    } finally {
      setSubmitting(false);
    }
  };

  const handlePresetSample = () => {
    setTitle('Post-Mortem: Postgres Connection Pool Starvation during Flash Sale');
    setService('postgres-primary');
    setContent(
      'Summary: At 14:00 UTC, a spike in checkout traffic caused 504 timeouts. Active Postgres connections hit 100% capacity.\n' +
      'Root Cause: Checkout service leaked idle DB connections due to missing timeout configuration in client pool.\n' +
      'Lessons Learned: Always deploy PgBouncer connection pooler in transaction mode. Add synthetic probes for pool saturation > 80%.\n' +
      'Action Items: Scale PgBouncer pool default_size to 50. Update Runbook RB-001.'
    );
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl space-y-4">
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <FileText className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Ingest Post-Mortem Document</h3>
              <p className="text-xs text-slate-400">Extracts lessons and retains into semantic memory</p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="px-5 pt-1">
          <button
            type="button"
            onClick={handlePresetSample}
            className="w-full py-1.5 px-3 rounded-lg bg-indigo-500/10 hover:bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 text-xs font-medium transition cursor-pointer"
          >
            <span>⚡ Load Sample Post-Mortem Text</span>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-5 pb-5 space-y-4 text-xs">
          {error && (
            <div className="p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300">
              {error}
            </div>
          )}

          <div className="space-y-1">
            <label className="text-slate-300 font-medium">Post-Mortem Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Post-Mortem: Postgres Connection Pool Saturation on Black Friday"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-indigo-500 text-xs"
            />
          </div>

          <div className="space-y-1">
            <label className="text-slate-300 font-medium">Primary Service *</label>
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
            <label className="text-slate-300 font-medium">Post-Mortem Text or Markdown *</label>
            <textarea
              rows={6}
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Paste RCA report, timeline analysis, and lessons learned..."
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
              <span>Ingest & Retain</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
