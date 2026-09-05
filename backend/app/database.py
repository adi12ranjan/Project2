"""
database.py — SQLite persistence layer.

Deliberately simple: the full structured analysis is stored as a JSON blob
in `analysis_json` (fast to build for a hackathon MVP), with a handful of
indexed columns for list/filter views. Swapping to Postgres later only means
changing the connection string and JSON column type — the schema concept
stays identical.
"""
import sqlite3
import json
import os

# Vercel's serverless filesystem is read-only except /tmp, and /tmp itself is
# wiped between cold starts (a fresh container = a fresh empty database).
# That's an acceptable tradeoff for a live hackathon demo session; a
# production deployment would swap this for a hosted Postgres using the same
# schema (see README).
if os.environ.get('VERCEL'):
    DB_PATH = '/tmp/forensics.db'
else:
    DB_PATH = os.path.join(os.path.dirname(__file__), 'forensics.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,
    filename TEXT,
    sender TEXT,
    recipient TEXT,
    subject TEXT,
    date_sent TEXT,
    message_id TEXT,
    threat_score INTEGER,
    classification TEXT,
    confidence INTEGER,
    analysis_json TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS iocs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT,
    type TEXT,
    value TEXT,
    risk_level TEXT,
    FOREIGN KEY(investigation_id) REFERENCES investigations(id)
);

CREATE INDEX IF NOT EXISTS idx_investigations_classification ON investigations(classification);
CREATE INDEX IF NOT EXISTS idx_iocs_investigation ON iocs(investigation_id);
CREATE INDEX IF NOT EXISTS idx_iocs_value ON iocs(value);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def save_investigation(investigation_id, filename, parsed, risk, iocs, analysis: dict, created_at: str):
    conn = get_connection()
    conn.execute(
        """INSERT OR REPLACE INTO investigations
           (id, filename, sender, recipient, subject, date_sent, message_id,
            threat_score, classification, confidence, analysis_json, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            investigation_id, filename, parsed.get('from_addr'),
            ', '.join(parsed.get('to_list', [])), parsed.get('subject'),
            parsed.get('date_raw'), parsed.get('message_id'),
            risk['score'], risk['classification'], risk['confidence'],
            json.dumps(analysis), created_at,
        ),
    )
    conn.execute("DELETE FROM iocs WHERE investigation_id = ?", (investigation_id,))
    for ioc in iocs:
        conn.execute(
            "INSERT INTO iocs (investigation_id, type, value, risk_level) VALUES (?, ?, ?, ?)",
            (investigation_id, ioc['type'], ioc['value'], ioc['risk']),
        )
    conn.commit()
    conn.close()


def list_investigations(limit=100):
    conn = get_connection()
    rows = conn.execute(
        """SELECT id, filename, sender, recipient, subject, date_sent,
                  threat_score, classification, confidence, created_at
           FROM investigations ORDER BY created_at DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_investigation(investigation_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM investigations WHERE id = ?", (investigation_id,)).fetchone()
    conn.close()
    if not row:
        return None
    result = dict(row)
    result['analysis'] = json.loads(result.pop('analysis_json'))
    return result


def list_iocs(limit=500):
    conn = get_connection()
    rows = conn.execute(
        """SELECT iocs.*, investigations.subject as investigation_subject
           FROM iocs JOIN investigations ON iocs.investigation_id = investigations.id
           ORDER BY iocs.id DESC LIMIT ?""",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def dashboard_stats():
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) c FROM investigations").fetchone()['c']
    critical = conn.execute("SELECT COUNT(*) c FROM investigations WHERE classification='CRITICAL'").fetchone()['c']
    high = conn.execute("SELECT COUNT(*) c FROM investigations WHERE classification='HIGH RISK'").fetchone()['c']
    suspicious_domains = conn.execute(
        "SELECT COUNT(DISTINCT value) c FROM iocs WHERE type='domain' AND risk_level IN ('medium','high')"
    ).fetchone()['c']
    malicious_ips = conn.execute(
        "SELECT COUNT(DISTINCT value) c FROM iocs WHERE type='ip' AND risk_level='high'"
    ).fetchone()['c']
    recent = list_investigations(limit=8)
    conn.close()
    return {
        'emails_analyzed': total,
        'critical_threats': critical,
        'high_risk_threats': high,
        'suspicious_domains': suspicious_domains,
        'malicious_ips': malicious_ips,
        'recent_investigations': recent,
    }
