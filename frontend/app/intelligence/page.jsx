'use client';
import { useEffect, useState } from 'react';
import Badge from '../../components/Badge';
import { api } from '../../lib/api';

export default function IntelligencePage() {
  const [investigations, setInvestigations] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    api.listInvestigations().then(setInvestigations).catch((e) => setError(e.message));
  }, []);

  const groups = ['CRITICAL', 'HIGH RISK', 'SUSPICIOUS', 'SAFE'].map((cls) => ({
    cls,
    items: investigations.filter((i) => i.classification === cls),
  }));

  return (
    <>
      {error && <div className="glass-panel"><div className="empty-state">Couldn&apos;t reach the backend ({error}).</div></div>}

      {investigations.length === 0 && !error && (
        <div className="glass-panel"><div className="empty-state">No investigations yet. Analyze an email first.</div></div>
      )}

      {groups.map(
        (g) =>
          g.items.length > 0 && (
            <div className="glass-panel" key={g.cls}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
                <Badge classification={g.cls} />
                <span style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text-faint)' }}>
                  {g.items.length} email{g.items.length !== 1 ? 's' : ''}
                </span>
              </div>
              <table>
                <tbody>
                  {g.items.map((inv) => (
                    <tr key={inv.id}>
                      <td>
                        <div>{inv.subject || '(no subject)'}</div>
                        <div style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--text-faint)' }}>
                          {inv.sender} &rarr; {inv.recipient}
                        </div>
                      </td>
                      <td style={{ fontFamily: 'var(--mono)', textAlign: 'right' }}>{inv.threat_score}/100</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
      )}
    </>
  );
}
