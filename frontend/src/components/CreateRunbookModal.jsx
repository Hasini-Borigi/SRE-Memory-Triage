import React, { useState } from 'react';
import { X, BookOpen, Loader2, Plus, Trash2 } from 'lucide-react';
import { createRunbook } from '../api';

export default function CreateRunbookModal({ isOpen, onClose, onCreated }) {
  const [id, setId] = useState('RB-011');
  const [title, setTitle] = useState('');
  const [service, setService] = useState('postgres-primary');
  const [description, setDescription] = useState('');
  const [steps, setSteps] = useState([
    'Inspect service health and metrics dashboard',
    'Verify logs for critical exceptions or saturations',
    'Apply remediation and monitor error rates',
  ]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const handleStepChange = (index, value) => {
    const updated = [...steps];
    updated[index] = value;
    setSteps(updated);
  };

  const addStep = () => {
    setSteps([...steps, '']);
  };

  const removeStep = (index) => {
    if (steps.length <= 1) return;
    setSteps(steps.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!id || !title || !description) {
      setError('ID, Title, and Description are required.');
      return;
    }
    const cleanSteps = steps.filter(s => s.trim().length > 0);
    if (cleanSteps.length === 0) {
      setError('At least one execution step is required.');
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const rb = await createRunbook({
        id,
        title,
        service,
        description,
        steps: cleanSteps,
      });
      if (onCreated) onCreated(rb);
      onClose();
    } catch (err) {
      setError(err.message || 'Failed to create runbook');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg overflow-hidden shadow-2xl space-y-4">
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-lg bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">Create Standard Operating Runbook</h3>
              <p className="text-xs text-slate-400">Registers SOP into semantic memory</p>
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

          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1">
              <label className="text-slate-300 font-medium">Runbook ID *</label>
              <input
                type="text"
                value={id}
                onChange={(e) => setId(e.target.value)}
                placeholder="RB-011"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-cyan-500 text-xs font-mono"
              />
            </div>

            <div className="col-span-2 space-y-1">
              <label className="text-slate-300 font-medium">Target Service *</label>
              <select
                value={service}
                onChange={(e) => setService(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-cyan-500 text-xs font-mono"
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
          </div>

          <div className="space-y-1">
            <label className="text-slate-300 font-medium">Runbook Title *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Postgres Read Replica Lag Remediation"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-white outline-none focus:border-cyan-500 text-xs"
            />
          </div>

          <div className="space-y-1">
            <label className="text-slate-300 font-medium">Description *</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Purpose of this procedure and symptoms it addresses..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-white outline-none focus:border-cyan-500 text-xs"
            />
          </div>

          {/* Steps */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-slate-300 font-medium">Execution Procedure Steps *</label>
              <button
                type="button"
                onClick={addStep}
                className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-1 cursor-pointer"
              >
                <Plus className="w-3 h-3" />
                <span>Add Step</span>
              </button>
            </div>

            <div className="space-y-2 max-h-40 overflow-y-auto pr-1">
              {steps.map((step, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <span className="font-mono text-slate-500 text-xs w-4">{idx + 1}.</span>
                  <input
                    type="text"
                    value={step}
                    onChange={(e) => handleStepChange(idx, e.target.value)}
                    placeholder={`Step ${idx + 1}`}
                    className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-white outline-none focus:border-cyan-500 text-xs"
                  />
                  {steps.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeStep(idx)}
                      className="text-slate-500 hover:text-rose-400 p-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ))}
            </div>
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
              className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-medium transition text-xs flex items-center gap-1.5 disabled:opacity-50"
            >
              {submitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>Save & Index</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
