const BASE = '/api';

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  health: () => fetch(`${BASE}/health`).then(handle),
  listDemoEmails: () => fetch(`${BASE}/demo-emails`).then(handle),
  analyzeDemo: (demo_id) =>
    fetch(`${BASE}/analyze/demo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ demo_id }),
    }).then(handle),
  analyzeRaw: (raw_email, filename) =>
    fetch(`${BASE}/analyze/raw`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ raw_email, filename }),
    }).then(handle),
  analyzeUpload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return fetch(`${BASE}/analyze/upload`, { method: 'POST', body: formData }).then(handle);
  },
  dashboardStats: () => fetch(`${BASE}/dashboard/stats`).then(handle),
  listInvestigations: () => fetch(`${BASE}/investigations`).then(handle),
  getInvestigation: (id) => fetch(`${BASE}/investigations/${id}`).then(handle),
  getReportUrl: (id) => `${BASE}/investigations/${id}/report`,
  listIocs: () => fetch(`${BASE}/iocs`).then(handle),
};
