'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: 'M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z' },
  { href: '/investigation', label: 'Email Investigation', icon: 'M3 5h18v14H3zM3 7l9 6 9-6' },
  { href: '/intelligence', label: 'Threat Intelligence', icon: 'M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6z' },
  { href: '/iocs', label: 'IOC Explorer', icon: 'circle:11,11,7|M21 21l-4.3-4.3' },
  { href: '/reports', label: 'Reports', icon: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6' },
];

function NavIcon({ path }) {
  if (path.startsWith('circle:')) {
    const [circlePart, restPath] = path.split('|');
    const [cx, cy, r] = circlePart.replace('circle:', '').split(',');
    return (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx={cx} cy={cy} r={r} />
        <path d={restPath} />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d={path} />
    </svg>
  );
}

export default function Shell({ children }) {
  const pathname = usePathname();

  return (
    <div className="app">
      <nav className="sidebar">
        <div className="brand">
          <div className="brand-mark">
            <svg viewBox="0 0 24 24" fill="none">
              <path d="M3 6l9 6 9-6" stroke="#062327" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              <rect x="3" y="5" width="18" height="14" rx="2.5" stroke="#062327" strokeWidth="2" />
            </svg>
          </div>
          <div className="brand-text">
            <div className="t1">TraceMail AI</div>
            <div className="t2">FORENSIC INTELLIGENCE</div>
          </div>
        </div>

        <div className="nav">
          {NAV_ITEMS.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`nav-item ${pathname === item.href ? 'active' : ''}`}
            >
              <NavIcon path={item.icon} />
              {item.label}
            </Link>
          ))}
        </div>

        <div className="sidebar-foot">
          <span className="pulse-dot"></span>ENGINE ONLINE
          <br />
          Rule-based analysis · FastAPI backend
          <br />
          Next.js frontend
        </div>
      </nav>

      <div className="main">
        <div className="topbar">
          <div className="titles">
            <h1>TraceMail AI</h1>
            <p>AI-Powered Email Threat Detection &amp; Forensic Intelligence</p>
          </div>
          <div className="live-pill">
            <span className="pulse-dot"></span>DEMO MODE
          </div>
        </div>
        <div className="content">{children}</div>
      </div>
    </div>
  );
}
