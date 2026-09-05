const TYPE_COLUMN = { location: 0, ip: 1, domain: 2, sender: 3, email: 4, url: 5, recipient: 5 };
const RISK_COLOR = { high: '#FF5B5B', medium: '#F0A93E', low: '#35D08C' };

export default function ForensicGraph({ graph }) {
  if (!graph || !graph.nodes || graph.nodes.length === 0) {
    return <div className="empty-state">No graph data available.</div>;
  }

  const COL_W = 150;
  const ROW_H = 68;
  const PAD = 50;

  const columns = {};
  graph.nodes.forEach((n) => {
    const col = TYPE_COLUMN[n.type] ?? 3;
    if (!columns[col]) columns[col] = [];
    columns[col].push(n);
  });

  const positions = {};
  Object.entries(columns).forEach(([col, nodes]) => {
    nodes.forEach((n, i) => {
      positions[n.id] = { x: PAD + Number(col) * COL_W, y: PAD + i * ROW_H };
    });
  });

  const maxCol = Math.max(...Object.keys(columns).map(Number));
  const maxRows = Math.max(...Object.values(columns).map((a) => a.length));
  const width = Math.max(700, PAD * 2 + maxCol * COL_W + 40);
  const height = Math.max(260, PAD * 2 + Math.max(1, maxRows - 1) * ROW_H + 40);

  return (
    <div className="graph-wrap">
      <svg width={width} height={height}>
        {graph.edges.map((e, i) => {
          const s = positions[e.source];
          const t = positions[e.target];
          if (!s || !t) return null;
          const midX = (s.x + t.x) / 2;
          return (
            <path
              key={i}
              className="graph-line"
              d={`M ${s.x + 50} ${s.y} C ${midX} ${s.y}, ${midX} ${t.y}, ${t.x - 50} ${t.y}`}
            />
          );
        })}
        {graph.nodes.map((n) => {
          const p = positions[n.id];
          if (!p) return null;
          const color = RISK_COLOR[n.risk] || '#8B96A3';
          const label = (n.label || '').length > 16 ? n.label.slice(0, 15) + '\u2026' : n.label || '';
          return (
            <g key={n.id} transform={`translate(${p.x - 50}, ${p.y - 18})`}>
              <rect className={`graph-node-rect ${n.risk === 'high' ? 'hot' : ''}`} width="100" height="36" rx="9" strokeWidth="1.5" />
              <text x="8" y="14" fontSize="8" fill={color} fontFamily="IBM Plex Mono, monospace" fontWeight="700">
                {n.type.toUpperCase()}
              </text>
              <text x="8" y="27" fontSize="9" fill="#E7ECF2" fontFamily="IBM Plex Mono, monospace">
                {label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
