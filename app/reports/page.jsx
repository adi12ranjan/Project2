'use client';
import { useEffect, useState } from 'react';
import Badge from '../../components/Badge';
import { api } from '../../lib/api';

export default function ReportsPage() {
  const [investigations, setInvestigations] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api.listInvestigations().then(setInvestigations).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="glass-panel">
      <div className="panel-head"><h2>&#128196; Reports</h2></div>
      {error && <div className="empty-state">Couldn&apos;t reach the backend ({error}).</div>}
      {investigations.length === 0 && !error && <div className="empty-state">No investigations yet.</div>}

      {investigations.map((inv) => (
        <div key={inv.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '14px 0', borderBottom: '1px solid var(--border-soft)' }}>
          <div>
            <div style={{ fontSize: 12.5, fontWeight: 600 }}>{inv.subject || '(no subject)'}</div>
            <div style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--text-faint)', marginTop: 3 }}>
              #{inv.id} &middot; {inv.sender} &middot; {new Date(inv.created_at).toLocaleString()}
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <Badge classification={inv.classification} />
            <a className="btn small" href={api.getReportUrl(inv.id)} download={`report-${inv.id}.md`}>
              &#8615; Report
            </a>
          </div>
        </div>
      ))}
    </div>
  );
}
