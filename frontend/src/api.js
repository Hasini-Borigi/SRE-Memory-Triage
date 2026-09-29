const API_BASE = '/api';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Failed to fetch health');
  return res.json();
}

export async function fetchIncidents(params = {}) {
  const query = new URLSearchParams();
  if (params.service) query.append('service', params.service);
  if (params.severity) query.append('severity', params.severity);
  if (params.status) query.append('status', params.status);

  const res = await fetch(`${API_BASE}/incidents?${query.toString()}`);
  if (!res.ok) throw new Error('Failed to fetch incidents');
  return res.json();
}

export async function fetchIncident(id) {
  const res = await fetch(`${API_BASE}/incidents/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch incident ${id}`);
  return res.json();
}

export async function createIncident(data) {
  const res = await fetch(`${API_BASE}/incidents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create incident');
  return res.json();
}

export async function analyzeIncident(id) {
  const res = await fetch(`${API_BASE}/incidents/${id}/analyze`, {
    method: 'POST',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to analyze incident');
  }
  return res.json();
}

export async function submitFeedback(id, data) {
  const res = await fetch(`${API_BASE}/incidents/${id}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to submit feedback');
  return res.json();
}

export async function resolveIncident(id, data) {
  const res = await fetch(`${API_BASE}/incidents/${id}/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to resolve incident');
  return res.json();
}

export async function fetchRunbooks() {
  const res = await fetch(`${API_BASE}/runbooks`);
  if (!res.ok) throw new Error('Failed to fetch runbooks');
  return res.json();
}

export async function createRunbook(data) {
  const res = await fetch(`${API_BASE}/runbooks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create runbook');
  return res.json();
}

export async function fetchPostMortems() {
  const res = await fetch(`${API_BASE}/postmortems`);
  if (!res.ok) throw new Error('Failed to fetch post-mortems');
  return res.json();
}

export async function createPostMortem(data) {
  const res = await fetch(`${API_BASE}/postmortems`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error('Failed to create post-mortem');
  return res.json();
}

export async function searchMemory(query, filterType = null) {
  const params = new URLSearchParams({ q: query, limit: 10 });
  if (filterType && filterType !== 'all') params.append('filter_type', filterType);
  const res = await fetch(`${API_BASE}/memory/search?${params.toString()}`);
  if (!res.ok) throw new Error('Failed to search memory');
  return res.json();
}

export async function fetchAnalytics() {
  const res = await fetch(`${API_BASE}/analytics`);
  if (!res.ok) throw new Error('Failed to fetch analytics');
  return res.json();
}
