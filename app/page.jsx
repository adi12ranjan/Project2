'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import Badge from '../components/Badge';
import { api } from '../lib/api';

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api.dashboardStats().then(setStats).catch((e) => setError(e.message));
  }, []);

  return (
    <>
      {error && (
        <div className="glass-panel" style={{ marginBottom: 16 }}>
          <div className="empty-state">
            Couldn&apos;t reach the backend ({error}). Make sure the FastAPI server is running on port 8000.
          </div>
        </div>
      )}

      {stats && (
        <>
          <div className="stat-strip">
            <div className="stat-card cyan"><div className="label">EMAILS ANALYZED</div><div className="value">{stats.emails_analyzed}</div></div>
            <div className="stat-card red"><div className="label">CRITICAL THREATS</div><div className="value">{stats.critical_threats}</div></div>
            <div className="stat-card amber"><div className="label">SUSPICIOUS DOMAINS</div><div className="value">{stats.suspicious_domains}</div></div>
            <div className="stat-card red"><div className="label">MALICIOUS IPS</div><div className="value">{stats.malicious_ips}</div></div>
          </div>

          <div className="grid2">
            <div className="glass-panel">
              <div className="panel-head"><h2>&#128225; Recent Investigations</h2></div>
              {stats.recent_investigations.length === 0 ? (
                <div className="empty-state">
                  No investigations yet. <Link href="/investigation" style={{ color: 'var(--cyan)' }}>Analyze an email &rarr;</Link>
                </div>
              ) : (
                <table>
                  <thead><tr><th>Subject</th><th>Sender</th><th>Score</th><th>Verdict</th></tr></thead>
                  <tbody>
                    {stats.recent_investigations.map((inv) => (
                      <tr key={inv.id}>
                        <td>{inv.subject || '(no subject)'}</td>
                        <td style={{ fontFamily: 'var(--mono)', color: 'var(--text-dim)' }}>{inv.sender}</td>
                        <td style={{ fontFamily: 'var(--mono)' }}>{inv.threat_score}</td>
                        <td><Badge classification={inv.classification} size="sm" /></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
            <div className="glass-panel">
              <div className="panel-head"><h2>&#9889; Quick Start</h2></div>
              <p style={{ fontSize: 12.5, color: 'var(--text-dim)', lineHeight: 1.8, marginBottom: 16 }}>
                Head to <b>Email Investigation</b> to paste a suspicious email or load the built-in demo attack,
                then run the analysis pipeline to see the full forensic breakdown.
              </p>
              <Link href="/investigation" className="btn primary full">&#8594; Start Investigation</Link>
              <div className="disclaimer">This dashboard reflects investigations run in this session — it is not connected to live mail traffic.</div>
            </div>
          </div>
        </>
      )}
    </>
  );
}
