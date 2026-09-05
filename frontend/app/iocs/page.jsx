'use client';
import { useEffect, useState } from 'react';
import { api } from '../../lib/api';

const TYPES = ['all', 'ip', 'domain', 'url', 'email', 'hash'];

export default function IocsPage() {
  const [iocs, setIocs] = useState([]);
  const [typeFilter, setTypeFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    api.listIocs().then(setIocs).catch((e) => setError(e.message));
  }, []);

  const filtered = iocs.filter((ioc) => {
    if (typeFilter !== 'all' && ioc.type !== typeFilter) return false;
    if (search && !ioc.value.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="glass-panel">
      <div className="panel-head"><h2>&#128269; IOC Explorer</h2></div>
      {error && <div className="empty-state">Couldn&apos;t reach the backend ({error}).</div>}

      <div className="tab-row">
        {TYPES.map((t) => (
          <button key={t} className={`tab-btn ${typeFilter === t ? 'active' : ''}`} onClick={() => setTypeFilter(t)}>
            {t.toUpperCase()}
          </button>
        ))}
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search value..."
          style={{ marginLeft: 'auto', maxWidth: 220 }}
        />
      </div>

      {filtered.length === 0 ? (
        <div className="empty-state">No IOCs match this filter.</div>
      ) : (
        <table>
          <thead><tr><th>Type</th><th>Value</th><th>Note</th><th>Risk</th><th>From</th></tr></thead>
          <tbody>
            {filtered.map((ioc) => (
              <tr key={ioc.id}>
                <td style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--text-dim)' }}>{ioc.type.toUpperCase()}</td>
                <td style={{ fontFamily: 'var(--mono)' }}>{ioc.value}</td>
                <td style={{ color: 'var(--text-faint)' }}>{ioc.note || '\u2014'}</td>
                <td>
                  <span className={`ir ${ioc.risk_level}`} style={{ display: 'inline-block' }}>{ioc.risk_level}</span>
                </td>
                <td style={{ color: 'var(--text-faint)', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {ioc.investigation_subject}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
