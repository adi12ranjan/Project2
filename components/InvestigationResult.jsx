'use client';
import { useState } from 'react';
import ThreatGauge from './ThreatGauge';
import Badge from './Badge';
import ForensicGraph from './ForensicGraph';
import { api } from '../lib/api';

function AuthChip({ label, verdict }) {
  const v = (verdict || 'unknown').toLowerCase();
  const cls = v === 'pass' ? 'pass' : v === 'fail' || v === 'none' ? 'fail' : 'other';
  return (
    <div className="auth-chip">
      <div className="an">{label}</div>
      <div className={`av ${cls}`}>{v.toUpperCase()}</div>
    </div>
  );
}

function IocCard({ ioc }) {
  return (
    <div className="ioc-card">
      <div className="it">{ioc.type.toUpperCase()}</div>
      <div className="iv">{ioc.value}</div>
      <span className={`ir ${ioc.risk}`}>{ioc.risk.toUpperCase()}</span>
    </div>
  );
}

function ActionButton({ label, icon, colorClass, onDone }) {
  const [done, setDone] = useState(false);
  return (
    <div
      className={`action-btn ${colorClass} ${done ? 'done' : ''}`}
      onClick={() => {
        setDone(true);
        setTimeout(() => setDone(false), 1600);
      }}
    >
      <span className="aicon">{done ? '\u2713' : icon}</span>
      {done ? onDone : label}
    </div>
  );
}

export default function InvestigationResult({ result, onOpenReport }) {
  const r = result;
  const auth = r.authentication;

  return (
    <>
      <div className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 20 }}>
        <div>
          <div style={{ fontFamily: 'var(--mono)', fontSize: 10.5, color: 'var(--text-faint)' }}>
            INVESTIGATION #{r.investigation_id}
          </div>
          <div style={{ fontSize: 17, fontWeight: 700, marginTop: 6 }}>{r.parsed.subject || '(no subject)'}</div>
          <div style={{ color: 'var(--text-dim)', fontSize: 12.5, marginTop: 6 }}>
            From <span style={{ fontFamily: 'var(--mono)' }}>{r.parsed.from_addr}</span> to{' '}
            <span style={{ fontFamily: 'var(--mono)' }}>{(r.parsed.to_list || []).join(', ')}</span>
          </div>
          <div style={{ marginTop: 14 }}>
            <Badge classification={r.risk.classification} />
          </div>
        </div>
        <ThreatGauge score={r.risk.score} classification={r.risk.classification} />
      </div>

      <div className="glass-panel">
        <div className="panel-head">
          <h2>&#9888;&#65039; Detection Findings</h2>
          <span className="sub">confidence {r.risk.confidence}%</span>
        </div>
        {r.risk.reasons.length === 0 ? (
          <div className="empty-state">No threat signals detected.</div>
        ) : (
          r.risk.reasons.map((reason, i) => (
            <div className="reason-row" key={i}>
              <span className="reason-w">+{reason.weight}</span>
              <div>
                <div className="reason-cat">{reason.category}</div>
                <div className="reason-text">{reason.text}</div>
              </div>
            </div>
          ))
        )}
      </div>

      <div className="grid2">
        <div className="glass-panel">
          <div className="panel-head"><h2>&#128272; Authentication</h2></div>
          <div className="auth-grid">
            <AuthChip label="SPF" verdict={auth.spf} />
            <AuthChip label="DKIM" verdict={auth.dkim} />
            <AuthChip label="DMARC" verdict={auth.dmarc} />
          </div>
        </div>
        <div className="glass-panel">
          <div className="panel-head"><h2>&#127919; IOC Extraction ({r.iocs.length})</h2></div>
          <div className="ioc-grid" style={{ maxHeight: 220, overflowY: 'auto' }}>
            {r.iocs.map((ioc, i) => (
              <IocCard ioc={ioc} key={i} />
            ))}
          </div>
        </div>
      </div>

      <div className="grid2">
        <div className="glass-panel">
          <div className="panel-head"><h2>&#128737;&#65039; Forensic Trace</h2></div>
          <div className="trace">
            <div className="trace-node">Sender</div>
            <div className="trace-arrow">&#8595;</div>
            {r.relay_chain.map((hop, i) => (
              <div key={i}>
                <div className={`trace-node ${hop.suspicious ? 'danger' : hop.is_origin ? 'origin' : ''}`}>
                  {hop.ip || 'no IP'} {hop.is_origin ? '(origin)' : ''}
                  {hop.flags && hop.flags.length > 0 && (
                    <div style={{ fontSize: 10.5, marginTop: 4 }}>{hop.flags.join(' \u00b7 ')}</div>
                  )}
                </div>
                <div className="trace-arrow">&#8595;</div>
              </div>
            ))}
            <div className="trace-node">Recipient</div>
          </div>
        </div>
        <div className="glass-panel">
          <div className="panel-head">
            <h2>&#127760; Geolocation Intelligence</h2>
            <span className="sub">demo data — not real-time</span>
          </div>
          <div className="geo-panel">
            {r.geolocation[0] && (
              <>
                <div className="geo-pin"><div className="geo-ring"></div></div>
                <div className="geo-label">
                  <div className="gl-title">{r.geolocation[0].ip}</div>
                  {r.geolocation[0].city}, {r.geolocation[0].country}
                  <br />
                  {r.geolocation[0].isp}
                </div>
              </>
            )}
          </div>
          <div className="geo-note">Illustrative visualization from a bundled demo dataset — no live geolocation service is queried.</div>
        </div>
      </div>

      <div className="glass-panel">
        <div className="panel-head"><h2>&#128279; Investigation Graph</h2></div>
        <ForensicGraph graph={r.graph} />
      </div>

      <div className="glass-panel">
        <div className="panel-head"><h2>&#9889; Recommended Actions</h2></div>
        <div className="actions-grid">
          <ActionButton label="QUARANTINE EMAIL" icon="\u{1F512}" colorClass="a1" onDone="QUARANTINED" />
          <ActionButton label="BLOCK DOMAIN" icon="\u{1F6AB}" colorClass="a2" onDone="BLOCKED" />
          <ActionButton label="INVESTIGATE IP" icon="\u{1F50D}" colorClass="a3" onDone="FLAGGED" />
          <ActionButton label="ESCALATE INCIDENT" icon="\u{1F6A8}" colorClass="a4" onDone="ESCALATED" />
        </div>
      </div>

      <div className="glass-panel" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
        <div>
          <h2 style={{ fontSize: 14 }}>&#128203; Forensic Report</h2>
          <p style={{ fontSize: 11.5, color: 'var(--text-faint)', marginTop: 4 }}>Full incident report with recommended actions.</p>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn" onClick={onOpenReport}>&#128196; View Report</button>
          <a className="btn primary" href={api.getReportUrl(r.investigation_id)} download={`report-${r.investigation_id}.md`}>
            &#8615; Download
          </a>
        </div>
      </div>

      <div className="disclaimer">
        &#9888;&#65039; This is a hackathon prototype (PS-26106). Geolocation uses a bundled demo dataset, not a live service.
        All scores are produced by a transparent, explainable rule engine — no fabricated ML accuracy percentages.
      </div>
    </>
  );
}
