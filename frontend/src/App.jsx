import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import LiveIncidentView from './components/LiveIncidentView';
import IncidentHistoryView from './components/IncidentHistoryView';
import RunbookLibraryView from './components/RunbookLibraryView';
import MemoryExplorerView from './components/MemoryExplorerView';
import AnalyticsView from './components/AnalyticsView';
import CreateIncidentModal from './components/CreateIncidentModal';
import ResolveModal from './components/ResolveModal';
import PostMortemModal from './components/PostMortemModal';
import CreateRunbookModal from './components/CreateRunbookModal';
import { fetchHealth, fetchIncidents, fetchRunbooks } from './api';
import { Loader2 } from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('live');
  const [health, setHealth] = useState(null);
  const [incidents, setIncidents] = useState([]);
  const [runbooks, setRunbooks] = useState([]);
  const [selectedIncidentId, setSelectedIncidentId] = useState('INC-1026');
  const [resolvingIncident, setResolvingIncident] = useState(null);
  const [loading, setLoading] = useState(true);

  // Modals
  const [createIncidentOpen, setCreateIncidentOpen] = useState(false);
  const [resolveOpen, setResolveOpen] = useState(false);
  const [postMortemOpen, setPostMortemOpen] = useState(false);
  const [createRunbookOpen, setCreateRunbookOpen] = useState(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [healthData, incsData, rbsData] = await Promise.all([
        fetchHealth().catch(() => ({
          status: 'healthy',
          llm_provider: 'groq',
          llm_model: 'llama-3.3-70b-versatile',
          memory_backend: 'hindsight',
          groq_key_masked: 'gsk_****',
          hindsight_key_masked: 'hsk_****',
        })),
        fetchIncidents().catch(() => []),
        fetchRunbooks().catch(() => []),
      ]);
      setHealth(healthData);
      setIncidents(incsData);
      setRunbooks(rbsData);

      // Default to open incident INC-1026 if present
      if (incsData.length > 0) {
        const openInc = incsData.find(i => i.id === 'INC-1026') || incsData[0];
        setSelectedIncidentId(openInc.id);
      }
    } catch (err) {
      console.error('Failed to load initial data:', err);
    } finally {
      setLoading(false);
    }
  };

  const reloadIncidents = async () => {
    try {
      const incs = await fetchIncidents();
      setIncidents(incs);
    } catch (err) {
      console.error('Failed to reload incidents:', err);
    }
  };

  const reloadRunbooks = async () => {
    try {
      const rbs = await fetchRunbooks();
      setRunbooks(rbs);
    } catch (err) {
      console.error('Failed to reload runbooks:', err);
    }
  };

  const handleSelectIncident = (id) => {
    setSelectedIncidentId(id);
    setActiveTab('live');
  };

  const handleOpenResolve = (inc) => {
    setResolvingIncident(inc);
    setResolveOpen(true);
  };

  const handleIncidentCreated = (newInc) => {
    setIncidents(prev => [newInc, ...prev]);
    setSelectedIncidentId(newInc.id);
    setActiveTab('live');
  };

  const handleIncidentResolved = (updatedInc) => {
    setIncidents(prev => prev.map(i => i.id === updatedInc.id ? updatedInc : i));
    reloadRunbooks();
  };

  const handleRunbookCreated = (newRb) => {
    setRunbooks(prev => [newRb, ...prev]);
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        onOpenCreate={() => setCreateIncidentOpen(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {loading ? (
          <div className="py-32 text-center">
            <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mx-auto mb-4" />
            <h3 className="text-base font-bold text-white">Initializing Persistent Memory Triage...</h3>
            <p className="text-xs text-slate-400 mt-1">Connecting to Vectorize Hindsight and Groq Llama reasoning</p>
          </div>
        ) : (
          <>
            {activeTab === 'live' && (
              <LiveIncidentView
                incidents={incidents}
                selectedIncidentId={selectedIncidentId}
                onSelectIncident={setSelectedIncidentId}
                onOpenResolve={handleOpenResolve}
                refreshIncidents={reloadIncidents}
              />
            )}

            {activeTab === 'history' && (
              <IncidentHistoryView
                incidents={incidents}
                onSelectIncident={handleSelectIncident}
              />
            )}

            {activeTab === 'runbooks' && (
              <RunbookLibraryView
                runbooks={runbooks}
                onOpenCreateRunbook={() => setCreateRunbookOpen(true)}
              />
            )}

            {activeTab === 'memory' && (
              <MemoryExplorerView
                onOpenPostMortem={() => setPostMortemOpen(true)}
              />
            )}

            {activeTab === 'analytics' && (
              <AnalyticsView />
            )}
          </>
        )}
      </main>

      {/* Modals */}
      <CreateIncidentModal
        isOpen={createIncidentOpen}
        onClose={() => setCreateIncidentOpen(false)}
        onCreated={handleIncidentCreated}
      />

      <ResolveModal
        isOpen={resolveOpen}
        onClose={() => setResolveOpen(false)}
        incident={resolvingIncident}
        onResolved={handleIncidentResolved}
      />

      <PostMortemModal
        isOpen={postMortemOpen}
        onClose={() => setPostMortemOpen(false)}
        onCreated={() => {}}
      />

      <CreateRunbookModal
        isOpen={createRunbookOpen}
        onClose={() => setCreateRunbookOpen(false)}
        onCreated={handleRunbookCreated}
      />
    </div>
  );
}
