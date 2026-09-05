const COLORS = {
  CRITICAL: '#FF5B5B',
  'HIGH RISK': '#FF5B5B',
  SUSPICIOUS: '#F0A93E',
  SAFE: '#35D08C',
};

export default function ThreatGauge({ score, classification }) {
  const r = 66;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - score / 100);
  const color = COLORS[classification] || '#8B96A3';

  return (
    <div className="gauge-wrap">
      <svg width="190" height="190" viewBox="0 0 190 190">
        <circle cx="95" cy="95" r={r} fill="none" stroke="#1A222C" strokeWidth="15" />
        <circle
          cx="95"
          cy="95"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="15"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          transform="rotate(-90 95 95)"
          style={{ transition: 'stroke-dashoffset 0.9s cubic-bezier(.2,.8,.2,1)' }}
        />
      </svg>
      <div className="gauge-num" style={{ color }}>{score}</div>
      <div className="gauge-sub">/ 100 — THREAT SCORE</div>
    </div>
  );
}
